"""
Brave Web Search Assistant

A conversational AI assistant that provides comprehensive web search capabilities
using the Brave Search API through MCP integration.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient

# Load environment variables
load_dotenv()

def create_brave_search_agent():
    """Create a Brave Web Search assistant agent."""
    
    # Verify API key is configured
    brave_api_key = os.getenv("BRAVE_API_KEY")
    if not brave_api_key:
        raise ValueError("BRAVE_API_KEY environment variable is required")
    
    # Connect to Brave Search MCP server
    brave_mcp_client = MCPClient(lambda: stdio_client(
        StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-brave-search"],
            env={"BRAVE_API_KEY": brave_api_key}
        )
    ))
    
    return brave_mcp_client

def main():
    """Main function to run the Brave Web Search assistant."""
    
    try:
        # Create the MCP client
        brave_mcp_client = create_brave_search_agent()
        
        # Initialize everything within single MCP context
        with brave_mcp_client:
            # Get tools and create agent
            tools = brave_mcp_client.list_tools_sync()
            
            agent = Agent(
                tools=tools,
                system_prompt=f"""You are a helpful web search assistant powered by Brave Search.

Current date: {datetime.now().strftime('%B %d, %Y')}

IMPORTANT: Be efficient with searches. Use only 1-2 search queries maximum per user question.

Your capabilities include:
- Comprehensive web search across the internet
- Local business and place search
- Site-specific search filtering

When users ask questions:
1. Use ONE targeted search query to find relevant information
2. Only make a second search if the first results are insufficient
3. Provide comprehensive answers based on the search results
4. Include source citations when relevant
5. Always mention the current date context when discussing "recent" information

Always aim for efficiency - avoid multiple redundant searches."""
            )
            
            print("🔍 Brave Web Search Assistant")
            print("=" * 50)
            print("Ask me anything! I can search the web for you.")
            print("Examples:")
            print("- 'Search for recent AWS Lambda updates'")
            print("- 'Find pizza restaurants near Central Park'")
            print("- 'What are the latest AI developments?'")
            print("- 'Search for Python tutorials on GitHub'")
            print("\nType 'quit' to exit.\n")
            
            # Interactive loop
            while True:
                try:
                    user_input = input("You: ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', 'bye']:
                        print("👋 Goodbye!")
                        break
                    
                    if not user_input:
                        continue
                    
                    print("\n🤖 Assistant:")
                    response = agent(user_input)
                    print(f"{response}\n")
                    
                except KeyboardInterrupt:
                    print("\n👋 Goodbye!")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}\n")
                
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        print("Please check your BRAVE_API_KEY in the .env file")

if __name__ == "__main__":
    main()
