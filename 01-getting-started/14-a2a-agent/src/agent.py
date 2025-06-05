from typing import Literal


from strands import Agent
from strands.models import BedrockModel
from boto3 import Session
from strands_tools import calculator
from pydantic import BaseModel, ValidationError
import json
import re


sess = Session()


class ResponseFormat(BaseModel):
    """Respond to the user in this format."""

    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str


class ConversionAgent:
    """CurrencyAgent - a specialized assistant for currency convesions."""

    def __init__(self):
        example_format = ResponseFormat(
            status="completed", message="Your response here"
        )

        SYSTEM_INSTRUCTION = f"""
            You are a specialized assistant for mathematical conversions. 
            Your sole purpose is to use the 'calculator' tool to answer questions about conversions. 
            If the user asks about anything other than mathematical conversions,
            politely state that you cannot help with that topic and can only assist with math conversion-related queries. 
            Do not attempt to answer unrelated questions or use tools for other purposes.
            Set response status to input_required if the user needs to provide more information.
            Set response status to error if there is an error while processing the request.
            Set response status to completed if the request is complete.

            Respond in the following format using <json_out> tags:
            <json_out>
            {example_format.model_dump_json()}
            </json_out>
        """
        self.model = BedrockModel(
            model_id='us.anthropic.claude-3-7-sonnet-20250219-v1:0',
            boto_session=sess,
            temperature=0.01,
        )
        self.agent = Agent(
            system_prompt=SYSTEM_INSTRUCTION, model=self.model, tools=[calculator]
        )

    def invoke(self, query, context) -> str:
        return self.get_agent_response(query)


    def get_agent_response(self, query):
        result = self.agent(query)
        response_text = result.message["content"][0]["text"]
        
        # Extract JSON from between <json_out> tags
        json_pattern = r'<json_out>(.*?)</json_out>'
        json_match = re.search(json_pattern, response_text, re.DOTALL)
        
        if json_match:
            json_content = json_match.group(1).strip()
            try:
                response_data = json.loads(json_content)
                structured_response = ResponseFormat(**response_data)
            except (json.JSONDecodeError, ValidationError) as e:
                print(f"Parsing error: {e}")
                structured_response = ResponseFormat(
                    status="error", message="Unable to process response format"
                )
        else:
            print("No <json_out> tags found in response")
            structured_response = ResponseFormat(
                status="error", message="No JSON output tags found in response"
            )

        # Use the structured_response instead of undefined current_state
        if structured_response.status == "input_required":
            return {
                "is_task_complete": False,
                "require_user_input": True,
                "content": structured_response.message,
            }
        if structured_response.status == "error":
            return {
                "is_task_complete": False,
                "require_user_input": True,
                "content": structured_response.message,
            }
        if structured_response.status == "completed":
            return {
                "is_task_complete": True,
                "require_user_input": False,
                "content": structured_response.message,
            }

        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": "We are unable to process your request at the moment. Please try again.",
        }

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
