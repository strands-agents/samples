## ⚠️⚠️ PLEASE READ :  The script agent creates and executes the script that may perform changes to your environment, always execute it from a sandbox (sample attached in sandbox folder) with readonly permissions to avoid any issues ⚠️⚠️

from strands import Agent,tool
from strands.models.bedrock import BedrockModel
from strands_tools import calculator, file_read, shell,http_request,python_repl, editor, journal
from aws_document_agent import doc_retrieve as doc_agent
from strands_boto_agent import code_assistant
import os
os.environ["BYPASS_TOOL_CONSENT"] = "true"
os.environ["STRANDS_TOOL_CONSOLE_MODE"] = "disabled"


@tool
def report_generator(query: str) -> str:
    """
    Report generator agent which is used to generate a report for the given output from the coding agent

    Args:
        output from coding agent's script
    Returns:
        str: A summary of results and recommendations for the specified AWS service, extracted from output of coding agent.
        include summary at the start, details and recommendation after that, include resource names in details when possible.
       
    """




bedrock_model = BedrockModel(model_id="anthropic.claude-3-5-sonnet-20241022-v2:0", temperature=0.4)
agent = Agent(
    system_prompt="You are a helpful assistant.  Use the agents and tools to assist the user" \
    " when user asks for auditing a resource, first gather the best practices for that service or resource using doc agent" \
    "example : user asks to audit an s3 bucket, first get best practices for setting up s3 bucket" \
    "Once you best practices, use the coding agent to create and execute necessary code to audit the service " \
    "Finally generate a professional looking report from the output of the coding agents results",
    tools=[doc_agent,code_assistant,report_generator],
    model=bedrock_model
)

response = agent("audit my s3 bucket for best practice, bucket name is testingbucket101 in us-east-1 region")
print(response)
