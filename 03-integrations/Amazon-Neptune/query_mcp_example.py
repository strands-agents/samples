import argparse
import os
from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient
from dotenv import load_dotenv

load_dotenv()


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Amazon Neptune agent using strands Agent use_aws tool")
    parser.add_argument("prompt", help="Prompt to send to the agent")

    # Parse arguments
    args = parser.parse_args()


    query_mcp_client = MCPClient(lambda: stdio_client(StdioServerParameters(command="uvx", 
        args=["awslabs.amazon-neptune-mcp-server@latest"],
        env={"NEPTUNE_ENDPOINT": os.getenv("NEPTUNE_ENDPOINT")},
        )))

    with query_mcp_client:
        tools = query_mcp_client.list_tools_sync()


        # Create an agent with all tools
        agent = Agent(tools=tools, 
            system_prompt="""You are an agent that interacts with an Amazon Neptune database to run graph queries.
            Whenever you write queries you should first fetch the schema to ensure that you understand the correct labels and property names 
            as well as the appropriate casing of those names and values.
            """,
        )

        agent(args.prompt)

if __name__ == "__main__":
    main()