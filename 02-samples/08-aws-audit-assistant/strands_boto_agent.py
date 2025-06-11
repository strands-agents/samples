## ⚠️⚠️ PLEASE READ :  The script agent creates and executes the script that may perform changes to your environment, always execute it from a sandbox (sample attached in sandbox folder) with readonly permissions to avoid any issues ⚠️⚠️


from strands import Agent,tool
from strands.models.bedrock import BedrockModel
from strands_tools import calculator, file_read, shell,http_request,python_repl, editor, journal
from aws_document_agent import doc_retrieve as doc_agent
import os
os.environ["BYPASS_TOOL_CONSENT"] = "true"
os.environ["STRANDS_TOOL_CONSOLE_MODE"] = "disabled"
@tool
def code_assistant(query: str) -> str:
    """
    Coding assistant agent for python boto3, you will recieve a set of best practices for the service. your job is to create a boto script and audit if the service 
     is set up properly according to best practices. Do not make any changes to the environment, only report if the service is set up properly or not 
    Args:
        query: A request to the coding assistant, the query will contain aws service name and the task that needs to be performed.
        For example: "check if the s3 bucket is set up according to best practices"
    Returns:
        you will create a code by utilizing the tools, pick up the environment variables for access key and secret access key and execute the script.
        you will return the result of the output
    """
    bedrock_model = BedrockModel(model_id="anthropic.claude-3-5-sonnet-20241022-v2:0", temperature=0.4)

    agent = Agent(
        system_prompt="You are a coding assistant for boto3 python library. You can use the available tools to execute python code and get the output.",
        tools=[python_repl, file_read, shell, http_request, editor, journal],
        model=bedrock_model
    )
    response = agent(query)
    print("\n\n")
    return response




# bedrock_model = BedrockModel(model_id="anthropic.claude-3-5-sonnet-20241022-v2:0", temperature=0.4)
# agent = Agent(
#     system_prompt="You are a helpful assistant.  Use the agents and tools at your disposal to assist the user",
#     tools=[doc_agent,code_assistant],
#     model=bedrock_model
# )

# response = agent("can you check if my s3 bucket is set up according to best practices, bucket name is testingbucket101 in us-east-1 region")
# print(response)


