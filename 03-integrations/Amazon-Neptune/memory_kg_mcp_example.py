from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient

memory_mcp_client = MCPClient(lambda: stdio_client(StdioServerParameters(
    command="uvx", 
    args=["https://github.com/aws-samples/amazon-neptune-generative-ai-samples/releases/download/mcp-servers-v0.0.9-beta/neptune_memory_mcp_server-0.0.9-py3-none-any.whl"],
    env={"NEPTUNE_MEMORY_ENDPOINT": "<NEPTUNE ENDPOINT AS SPECIFIED HERE https://github.com/awslabs/mcp/tree/main/src/amazon-neptune-mcp-server>"}
)))
perplexity_mcp_client = MCPClient(lambda: stdio_client(StdioServerParameters(command="npx", 
    args=["server-perplexity-ask"],
    env={"PERPLEXITY_API_KEY": "<INSERT PERPLEXITY AI KEY>"},
    )))
with memory_mcp_client, perplexity_mcp_client:
    tools = memory_mcp_client.list_tools_sync() + perplexity_mcp_client.list_tools_sync()
    agent = Agent(tools=tools, 
        system_prompt="""
        You are a research agent. Your role is to:
            1. Analyze incoming research questions, search your own information as well as web information to find and propose answers           
            2. As you research and find information store the important entities, observations, and relations in my memory knowlege graph
            3. At the end of your research provide a brief summary of your findings and the knowledge graph entities you used to back those findings
        """)
    agent("""I work on the Amazon Neptune team.  I am currently building and testing MCP servers with
            the Strands Agent SDK to show how you can Amazon Neptune with an agent framework to store memories in the form of a knowledge graph.
          
            I am interested in what key considerations I should take into account?
            """)
