from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from strands_tools import current_time
from pydantic import BaseModel
import uvicorn
from strands import Agent, tool
import boto3
import json
from uuid import uuid4
import os

# Import my tools
from tools import get_tables_information, load_file_content
from postgresql_query_utils import run_sql_query_on_postgresql
from strands.models import BedrockModel
from utils import save_raw_query_result
from utils import read_messages_by_session
from utils import save_messages

# Initialize the FastAPI application
app = FastAPI(title="Data Analyst Assistant API")

# CORS middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_system_prompt():
    """
    Load the system prompt from a file or return a fallback prompt if the file is not available.
    
    Returns:
        str: The system prompt to use for the data analyst assistant
    """
    fallback_prompt = """You are a helpful Data Analyst Assistant who can help with data analysis tasks.
                You can process data, interpret statistics, and provide insights based on data."""
    return load_file_content("instructions.txt", default_content=fallback_prompt)

# Load the system prompt
DATA_ANALYST_SYSTEM_PROMPT = load_system_prompt()

@app.get('/health')
def health_check():
    """
    Health check endpoint for the load balancer.

    Returns:
        dict: A status message indicating the service is healthy
    """
    return {"status": "healthy"}


async def run_data_analyst_assistant_with_stream_response(bedrock_model, system_prompt: str, prompt: str, prompt_uuid: str, session_id: str):
    """
    Run the data analyst assistant and stream the response.

    Args:
        bedrock_model: The LLM model to use
        system_prompt (str): The system prompt for the agent
        prompt (str): The user's prompt
        prompt_uuid (str): Unique identifier for the prompt
        session_id (str): Session identifier for conversation context

    Yields:
        str: Chunks of the response as they become available
    """
    user_prompt = prompt
    user_prompt_uuid = prompt_uuid
    user_session_id = session_id

    @tool
    def execute_sql_query(sql_query: str, description: str) -> str:
        """
        Execute an SQL query against a database and return results for data analysis

        Args:
            sql_query: The SQL query to execute
            description: Concise explanation of the SQL query

        Returns:
            str: JSON string containing the query results or error message
        """
        nonlocal user_prompt
        nonlocal user_prompt_uuid
        try:
            # Execute the SQL query using the existing function
            # But we need to parse the response first
            response_json = json.loads(run_sql_query_on_postgresql(sql_query))
            
            # Check if there was an error
            if "error" in response_json:
                return json.dumps(response_json)
            
            # Extract the results
            records_to_return = response_json.get("result", [])
            message = response_json.get("message", "")
            
            # Prepare result object
            if message != "":
                result = {
                    "result": records_to_return,
                    "message": message
                }
            else:
                result = {
                    "result": records_to_return
                }
            
            # Save to DynamoDB using the new function
            save_result = save_raw_query_result(
                user_prompt_uuid,
                user_prompt,
                sql_query,
                description,
                result,
                message
            )
            
            if not save_result["success"]:
                result["saved"] = False
                result["save_error"] = save_result["error"]
                
            return json.dumps(result)
                
        except Exception as e:
            return json.dumps({"error": f"Unexpected error: {str(e)}"})

    # Get conversation history
    message_history = read_messages_by_session(user_session_id)
    if len(message_history) > 0:
        starting_message_id = len(message_history)
    else:
        starting_message_id = 0
    print("Message history length: " + str(len(message_history)))
    print("Messages: " + str(message_history))

    # Initialize the data analyst agent
    data_analyst_agent = Agent(
        messages=message_history,
        model=bedrock_model,
        system_prompt=system_prompt,
        tools=[get_tables_information, current_time, execute_sql_query],
        callback_handler=None
    )

    # Stream the response
    async for item in data_analyst_agent.stream_async(prompt):
        if "message" in item and "content" in item["message"] and "role" in item["message"] and item["message"]["role"]=="assistant":
            for content_item in item['message']['content']:
                if "toolUse" in content_item and "input" in content_item["toolUse"] and content_item["toolUse"]['name']=='execute_sql_query':
                    yield f" {content_item["toolUse"]["input"]["description"]}.\n\n"
                elif "toolUse" in content_item and "name" in content_item["toolUse"] and content_item["toolUse"]['name']=='get_tables_information':
                    yield "\n\n"
                elif "toolUse" in content_item and "name" in content_item["toolUse"] and content_item["toolUse"]['name']=='current_time':
                    yield "\n\n"
        elif "data" in item:
            yield item['data']

    # Save the conversation
    save_messages(user_session_id, user_prompt_uuid, starting_message_id, data_analyst_agent.messages)


class PromptRequest(BaseModel):
    """
    Request model for the assistant API endpoint.

    Attributes:
        bedrock_model_id (str): The ID of the Bedrock model to use
        prompt (str): The user's prompt
        prompt_uuid (str, optional): Unique identifier for the prompt
        user_timezone (str, optional): User's timezone
        session_id (str, optional): Session identifier for conversation context
    """
    bedrock_model_id: str = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    prompt: str  # Required
    prompt_uuid: str = None  # Optional with None as default
    user_timezone: str = None  # Optional with a default value
    session_id: str = None  # Optional with None as default

@app.post('/assistant-streaming')
async def assistant_streaming(request: PromptRequest):
    """
    Endpoint to stream the data analysis as it comes in, not all at once at the end.

    Args:
        request (PromptRequest): The request containing the prompt and other parameters

    Returns:
        StreamingResponse: A streaming response with the assistant's output

    Raises:
        HTTPException: If the request is invalid or if an error occurs
    """
    try:
        print("Request received: ")
        print(request)

        prompt = request.prompt
        if not prompt:
            raise HTTPException(status_code=400, detail="No prompt provided")

        prompt_uuid = request.prompt_uuid
        if not prompt_uuid:
            prompt_uuid = str(uuid4())

        user_timezone = request.user_timezone
        if not user_timezone:
            user_timezone = "US/Pacific"

        session_id = request.session_id
        if not session_id:
            session_id = str(uuid4())

        bedrock_model_id = request.bedrock_model_id

        # Create a Bedrock model with the custom session
        bedrock_model = BedrockModel(
            model_id=bedrock_model_id
        )

        print("Values: ")
        print(f"Prompt: {prompt}")
        print(f"Prompt UUID: {prompt_uuid}")
        print(f"User Timezone: {user_timezone}")
        print(f"Session ID: {session_id}")

        system_prompt = DATA_ANALYST_SYSTEM_PROMPT.replace("{timezone}", user_timezone)

        return StreamingResponse(
            run_data_analyst_assistant_with_stream_response(bedrock_model, system_prompt, prompt, prompt_uuid, session_id),
            media_type="text/plain"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    # Get port from environment variable or default to 8000
    port = int(os.environ.get('PORT', 8000))
    print(f"Starting Data Analyst Assistant.")
    uvicorn.run(app, host='0.0.0.0', port=port)