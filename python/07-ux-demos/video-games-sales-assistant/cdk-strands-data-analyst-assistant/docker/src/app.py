from strands import Agent, tool
from strands.models import BedrockModel
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import boto3
import json
from uuid import uuid4
from datetime import datetime, timezone
import os

# Import my tools
from tools import run_sql_query, get_tables_information
from utils import load_file_content, save_raw_query_result, read_messages_by_session, save_messages, load_config
from utils import validate_cognito_token_with_config, extract_bearer_token

# Load configuration from SSM Parameter Store
# Get PROJECT_ID from environment variable to construct SSM parameter paths
PROJECT_ID = os.environ.get('PROJECT_ID', 'strands-data-analyst-assistant')

# Load all configuration from SSM
try:
    config = load_config()
    print(f"\n✅ CONFIGURATION LOADED FROM SSM")
    print("-" * 50)
    print(f"🔧 Project ID: {PROJECT_ID}")
    print(f"📊 Database: {config.get('DATABASE_NAME')}")
    print("-" * 50)
except Exception as e:
    print(f"\n❌ CONFIGURATION LOAD ERROR")
    print("-" * 50)
    print(f"🚨 Error: {e}")
    print(f"🔧 Project ID: {PROJECT_ID}")
    print("-" * 50)
    # Set empty config as fallback
    config = {}

# Initialize the FastAPI application
app = FastAPI(title="Data Analyst Assistant API")

# CORS middleware to allow web application origin
web_app_url = os.environ.get('WEB_APPLICATION_URL', 'http://localhost:3000')
app.add_middleware(
    CORSMiddleware,
    allow_origins=[web_app_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@tool
def current_time() -> str:
    """Get the current UTC date and time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def load_system_prompt():
    """
    Load the system prompt from the instructions.txt file.
    
    This prompt defines the behavior and capabilities of the data analyst assistant.
    If the file is not available, a fallback prompt is used.
    
    Returns:
        str: The system prompt to use for the data analyst assistant
    """
    print("\n" + "="*50)
    print("📝 LOADING SYSTEM PROMPT")
    print("="*50)
    print("📂 Attempting to load instructions.txt...")
    
    fallback_prompt = """You are a helpful Data Analyst Assistant who can help with data analysis tasks.
                You can process data, interpret statistics, and provide insights based on data."""
    
    try:
        prompt = load_file_content("instructions.txt", default_content=fallback_prompt)
        if prompt == fallback_prompt:
            print("⚠️  Using fallback prompt (instructions.txt not found)")
        else:
            print("✅ Successfully loaded system prompt from instructions.txt")
            print(f"📊 Prompt length: {len(prompt)} characters")
        print("="*50 + "\n")
        return prompt
    except Exception as e:
        print(f"❌ Error loading system prompt: {str(e)}")
        print("⚠️  Using fallback prompt")
        print("="*50 + "\n")
        return fallback_prompt

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
            response_json = json.loads(run_sql_query(sql_query))
            
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
    message_history = read_messages_by_session(
        session_id, 
        config.get('LAST_NUMBER_OF_MESSAGES', 20)
    )
    if len(message_history) > 0:
        starting_message_id = len(message_history)
    else:
        starting_message_id = 0
    print(f"\n📚 CONVERSATION HISTORY")
    print("-" * 40)
    print(f"📊 Messages loaded: {len(message_history)}")
    print(f"🔗 Session ID: {session_id}")
    print(f"🆔 Starting message ID: {starting_message_id}")
    print("-" * 40)

    # Initialize the data analyst agent
    data_analyst_agent = Agent(
        messages=message_history,
        model=bedrock_model,
        system_prompt=system_prompt,
        tools=[current_time, get_tables_information, execute_sql_query],
        callback_handler=None
    )

    # Stream the response to the client
    stream = data_analyst_agent.stream_async(prompt)

    async for event in stream:            
        if "message" in event and "content" in event["message"] and "role" in event["message"] and event["message"]["role"] == "assistant":
            for content_item in event['message']['content']:
                if "toolUse" in content_item and "input" in content_item["toolUse"] and content_item["toolUse"]['name'] == 'execute_sql_query':
                    yield f" {content_item['toolUse']['input']['description']}.\n\n"
                elif "toolUse" in content_item and "name" in content_item["toolUse"] and content_item["toolUse"]['name'] == 'get_tables_information':
                    yield "\n\n"
                elif "toolUse" in content_item and "name" in content_item["toolUse"] and content_item["toolUse"]['name'] == 'current_time':
                    yield "\n\n"
        elif "data" in event:
            yield event['data']


    # Save the conversation
    save_messages(
        session_id, 
        user_prompt_uuid, 
        starting_message_id, 
        data_analyst_agent.messages
    )

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
    bedrock_model_id: str = None  # Optional, will use config default if not provided
    prompt: str  # Required
    prompt_uuid: str = None  # Optional with None as default
    user_timezone: str = None  # Optional with a default value
    session_id: str = None  # Optional with None as default

@app.post('/assistant-streaming')
async def assistant_streaming(
    request: PromptRequest, 
    authorization: str = Header(None, description="Bearer token for authentication (format: 'Bearer <token>')")
):
    """
    Endpoint to stream the data analysis as it comes in, not all at once at the end.

    Args:
        request (PromptRequest): The request containing the prompt and other parameters
        authorization (str, optional): Authorization header containing the Bearer token.
                                     Format: "Bearer <jwt-token>"
                                     Required only when Cognito authentication is configured.
                                     If Cognito parameters are set to "N/A", authentication is skipped.

    Returns:
        StreamingResponse: A streaming response with the assistant's output

    Raises:
        HTTPException: If the request is invalid, authentication fails, or if an error occurs
    """
    try:
        # Check if Cognito is configured before attempting authentication
        cognito_user_pool_id = os.environ.get('COGNITO_USER_POOL_ID', 'N/A')
        
        # Skip authentication if Cognito is not configured (N/A values)
        if ( cognito_user_pool_id == "N/A"):
            
            print(f"\n⚠️  COGNITO NOT CONFIGURED - SKIPPING AUTHENTICATION")
            print("-" * 50)
            print(f"🔧 COGNITO_USER_POOL_ID: {cognito_user_pool_id}")
            print("-" * 50)
        else:
            # Cognito is configured, validate the token
            try:
                # Extract token from Authorization header
                token = extract_bearer_token(authorization)
                if not token:
                    raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
                
                # Validate the token using SSM configuration
                decoded_token = validate_cognito_token_with_config(token)
                if not decoded_token:
                    raise HTTPException(status_code=401, detail="Invalid or expired token")
                
                print(f"\n🔐 AUTHENTICATED USER")
                print("-" * 40)
                print(f"👤 Username: {decoded_token.get('username', 'unknown')}")
                print(f"📧 Email: {decoded_token.get('email', 'unknown')}")
                print(f"🔑 Token Use: {decoded_token.get('token_use', 'unknown')}")
                print("-" * 40)
                
            except Exception as cognito_error:
                print(f"\n❌ AUTHENTICATION FAILED")
                print("-" * 40)
                print(f"🚨 Error: {cognito_error}")
                print("-" * 40)
                raise HTTPException(status_code=401, detail=str(cognito_error))
        print(f"\n🚀 NEW REQUEST RECEIVED")
        print("=" * 50)
        print(f"📝 Prompt: {request.prompt[:100]}{'...' if len(request.prompt) > 100 else ''}")
        print(f"🤖 Model: {request.bedrock_model_id}")
        print("=" * 50)
    
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

        bedrock_model_id = request.bedrock_model_id or 'us.anthropic.claude-sonnet-4-6'
        
        print(f"\n🔧 REQUEST PROCESSING")
        print("-" * 40)
        print(f"🆔 Prompt UUID: {prompt_uuid}")
        print(f"🌍 Timezone: {user_timezone}")
        print(f"🔗 Session ID: {session_id}")
        print(f"🤖 Model ID: {bedrock_model_id}")
        print("-" * 40)

        # Create a Bedrock model with the custom session
        bedrock_model = BedrockModel(
            model_id=bedrock_model_id
        )

        system_prompt = DATA_ANALYST_SYSTEM_PROMPT.replace("{timezone}", user_timezone)

        return StreamingResponse(
            run_data_analyst_assistant_with_stream_response(bedrock_model, system_prompt, prompt, prompt_uuid, session_id),
            media_type="text/plain"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def main():
    """Entry point for the Data Analyst Assistant application."""
    port = int(os.environ.get('PORT', '8000'))
    project_id = os.environ.get('PROJECT_ID', 'strands-data-analyst-assistant')
    
    print(f"\n🚀 STARTING DATA ANALYST ASSISTANT")
    print("=" * 50)
    print(f"🌐 Host: 0.0.0.0")
    print(f"🔌 Port: {port}")
    print(f"🔧 Project ID: {project_id}")
    print("=" * 50)
    
    uvicorn.run(
        app, 
        host='0.0.0.0', 
        port=port,
        timeout_keep_alive=300,
        timeout_graceful_shutdown=30,
        limit_max_requests=1000,
    )

if __name__ == "__main__":
    main()