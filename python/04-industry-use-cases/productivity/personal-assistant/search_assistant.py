import os
from dotenv import load_dotenv
from mcp import StdioServerParameters, stdio_client
from strands import Agent, tool
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from constants import SESSION_ID

# Load environment variables
load_dotenv()

# Show rich UI for tools in CLI
os.environ["STRANDS_TOOL_CONSOLE_MODE"] = "enabled"


@tool
def search_assistant(query: str) -> str:
    """
    Search assistant agent for handling general queries
    Args:
        query: A request to the search assistant

    Returns:
        Output from interaction
    """
    # Reuse the already initialized MCP server connection
    response = agent(query)
    print("\n\n")
    return response


PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
if not PERPLEXITY_API_KEY:
    raise ValueError("PERPLEXITY_API_KEY environment variable is required")

try:
    # Initialize Perplexity MCP server
    perplexity_mcp_server = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="docker",
                args=[
                    "run",
                    "-i",
                    "--rm",
                    "-e",
                    "PERPLEXITY_API_KEY",
                    "mcp/perplexity-ask",
                ],
                env={"PERPLEXITY_API_KEY": PERPLEXITY_API_KEY},
            )
        )
    )
except Exception as e:
    raise Exception(f"Failed to initialize MCP Client: {str(e)}")


system_prompt = """You are an intelligent search and research assistant with access to real-time web information.

    Your capabilities include:
    - Searching the web for current information and news
    - Researching topics across various domains
    - Providing accurate, up-to-date answers with reliable sources
    - Synthesizing information from multiple sources
    - Fact-checking and verification

    When responding:
    - Always cite your sources when possible
    - Distinguish between factual information and opinions
    - Provide comprehensive yet concise answers
    - If information is uncertain or contradictory, mention this
    - Suggest follow-up questions when appropriate
    - Focus on accuracy and reliability

    For research queries:
    1. Search for the most current and relevant information
    2. Cross-reference multiple sources when possible
    3. Provide context and background information
    4. Summarize key findings clearly
    5. Highlight any limitations or uncertainties in the data"""

# Initialize the MCP server connection once and reuse it
perplexity_mcp_server.__enter__()

try:
    model = BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    )
    # Get available tools from MCP server
    tools = perplexity_mcp_server.list_tools_sync()

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=tools,
        trace_attributes={"session.id": SESSION_ID},
    )
except Exception as e:
    perplexity_mcp_server.__exit__(None, None, None)
    raise e


if __name__ == "__main__":
    print("====================================================================================")
    print("🔍  WELCOME TO YOUR PERSONAL SEARCH ASSISTANT  🔍")
    print("====================================================================================")
    print("🌐 I'm your intelligent research companion ready to help with:")
    print("   🔎 Real-time web searches and information lookup")
    print("   📰 Current news and trending topics")
    print("   📚 Research across diverse topics and domains")
    print("   ✅ Fact-checking and source verification")
    print("   📊 Data analysis and information synthesis")
    print("   🎯 Targeted research with reliable sources")
    print()
    print("🛠️  Powered by:")
    print("   • Perplexity AI - Advanced web search capabilities")
    print("   • Real-time information access")
    print("   • Multi-source cross-referencing")
    print("   • Source citation and verification")
    print()
    print("💡 Tips:")
    print("   • Ask specific questions for better results")
    print("   • Request sources when you need citations")
    print("   • Try: 'What's the latest news about...' or 'Research...'")
    print("   • I can help with current events, facts, and analysis")
    print()
    print("🚪 Type 'exit' to quit anytime")
    print("====================================================================================")
    print()

    # Run the agent in a loop for interactive conversation
    while True:
        try:
            user_input = input("🔍 You: ").strip()
            if not user_input:
                print("💭 Please ask me a question or type 'exit' to quit")
                continue

            if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                print()
                print("========================================================")
                print("👋 Thanks for exploring with me!")
                print("🌐 Keep discovering and learning!")
                print("🔍 See you next time!")
                print("========================================================")
                break
            print("🤖 SearchBot: ", end="")
            try:
                response = search_assistant(user_input)
            except Exception as e:
                print(f"❌ Error processing search query: {str(e)}")
                print("🔧 Please try rephrasing your question or check your connection")
        except KeyboardInterrupt:
            print("\n")
            print("============================================================")
            print("👋 Search Assistant interrupted!")
            print("🌐 Thanks for researching with me!")
            print("🔍 Happy exploring!")
            print("============================================================")
            break
        except Exception as e:
            print(f"❌ An error occurred: {str(e)}")
            print("🔧 Please try again or type 'exit' to quit")
            print()