import os

from mcp import StdioServerParameters, stdio_client
from strands import Agent, tool
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from strands_tools import file_write

@tool
def aws_cost_assistant(query: str) -> str:
    """
    Process and respond AWS cost related queries.

    Args:
        query: The user's question

    Returns:
        A helpful response addressing user query
    """

    bedrock_model = BedrockModel(model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0")

    response = str()

    try:
        env = {}
        if os.getenv("BEDROCK_LOG_GROUP_NAME") is not None:
            env["BEDROCK_LOG_GROUP_NAME"] = os.getenv("BEDROCK_LOG_GROUP_NAME")
        cost_mcp_server = MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command="uvx",
                    args=["awslabs.cost-explorer-mcp-server@latest"],
                    env=env,
                )
            )
        )

        with cost_mcp_server:

            tools = cost_mcp_server.list_tools_sync() + [file_write]
            # Create the research agent with specific capabilities
            cost_agent = Agent(
                model=bedrock_model,
                system_prompt="""You are a AWS account cost analyst. You can do the following tasks:
                - Amazon EC2 Spend Analysis: View detailed breakdowns of EC2 spending for the last day
                - Amazon Bedrock Spend Analysis: View breakdown by region, users and models over the last 30 days
                - Service Spend Reports: Analyze spending across all AWS services for the last 30 days
                - Detailed Cost Breakdown: Get granular cost data by day, region, service, and instance type
                - Interactive Interface: Use Claude to query your cost data through natural language
                """,
                tools=tools,
            )
            response = str(cost_agent(query))
            print("\n\n")

        if len(response) > 0:
            return response

        return "I apologize, but I couldn't properly analyze your question. Could you please rephrase or provide more context?"

    except Exception as e:
        return f"Error processing your query: {str(e)}"


if __name__ == "__main__":
    aws_cost_assistant("Get my usage of last 7 days per service")
