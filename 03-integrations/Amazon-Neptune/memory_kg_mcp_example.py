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
    memory_mcp_client = MCPClient(lambda: stdio_client(StdioServerParameters(
        command="uvx", 
        args=["https://github.com/aws-samples/amazon-neptune-generative-ai-samples/releases/download/mcp-servers-v0.0.9-beta/neptune_memory_mcp_server-0.0.9-py3-none-any.whl"],
        env={"NEPTUNE_MEMORY_ENDPOINT": os.getenv("NEPTUNE_MEMORY_ENDPOINT")}
    )))
    perplexity_mcp_client = MCPClient(lambda: stdio_client(StdioServerParameters(command="npx", 
        args=["server-perplexity-ask"],
        env={"PERPLEXITY_API_KEY": os.getenv("PERPLEXITY_API_KEY")},
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
        agent(args.prompt)

if __name__ == "__main__":
    main()
