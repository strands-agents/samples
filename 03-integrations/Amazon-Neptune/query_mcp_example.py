from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient


query_mcp_client = MCPClient(lambda: stdio_client(StdioServerParameters(command="uvx", 
    args=["awslabs.amazon-neptune-mcp-server@latest"],
    env={"NEPTUNE_ENDPOINT": "<NEPTUNE ENDPOINT AS SPECIFIED HERE https://github.com/awslabs/mcp/tree/main/src/amazon-neptune-mcp-server>"},
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

    agent("Find me a flight from Anchorage to New York that goes through Chicago?")