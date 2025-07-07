#!/usr/bin/env python3
"""
Web Search Agent with DuckDuckGo

This agent demonstrates how to create a Strands agent with real-time web search capabilities
using DuckDuckGo's search API. The agent can answer questions that require current information
by searching the web and providing contextual responses.
"""

from strands import Agent, tool
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException, DuckDuckGoSearchException
import logging

# Configure logging for better debugging
logging.getLogger("strands").setLevel(logging.INFO)


@tool
def websearch(keywords: str, region: str = "us-en", max_results: int = 5) -> str:
    """
    Search the web to get updated information using DuckDuckGo.
    
    Args:
        keywords (str): The search query keywords
        region (str): The search region (us-en, uk-en, etc.)
        max_results (int): Maximum number of search results to return
        
    Returns:
        str: Search results or error message
    """
    try:
        print(f"🔍 Searching for: {keywords}")
        results = DDGS().text(keywords, region=region, max_results=max_results)
        
        if not results:
            return "No search results found for the given query."
            
        # Format results for better readability
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append(
                f"{i}. **{result.get('title', 'No title')}**\n"
                f"   {result.get('body', 'No description')}\n"
                f"   Source: {result.get('href', 'No URL')}"
            )
        
        return "\n\n".join(formatted_results)
        
    except RatelimitException:
        return "Search rate limit exceeded. Please try again after a short delay."
    except DuckDuckGoSearchException as e:
        return f"Search service error: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


def create_websearch_agent() -> Agent:
    """
    Create and configure the web search agent.
    
    Returns:
        Agent: Configured Strands agent with web search capabilities
    """
    system_prompt = """You are a helpful AI assistant with real-time web search capabilities.
    
    Your primary function is to help users find current, accurate information on any topic by 
    searching the web when needed. You should:
    
    1. Use the websearch tool when users ask about:
       - Current events, news, or recent developments
       - Real-time information (weather, stock prices, etc.)
       - Specific facts that might change over time
       - Recent research or studies
       - Any topic where you need the most up-to-date information
    
    2. Provide clear, well-structured responses based on search results
    3. Always cite your sources when presenting information from search results
    4. If search results are insufficient, let the user know and suggest alternative approaches
    
    Be conversational, helpful, and always strive to provide the most current and accurate information."""
    
    agent = Agent(
        system_prompt=system_prompt,
        tools=[websearch]
    )
    
    return agent


def main():
    """Main function to run the web search agent interactively."""
    agent = create_websearch_agent()
    
    print("\n🌐 Web Search Agent")
    print("=" * 50)
    print("I can help you find current information on any topic!")
    print("Ask me about news, weather, recent developments, or anything you'd like to know.")
    print("Type 'exit' to quit.\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\nThanks for using the Web Search Agent! 👋")
                break
                
            if not user_input:
                print("Please enter a question or 'exit' to quit.")
                continue
            
            print("\n🤖 Agent:", end=" ")
            response = agent(user_input)
            print(f"{response}\n")
            
        except KeyboardInterrupt:
            print("\n\nThanks for using the Web Search Agent! 👋")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again or type 'exit' to quit.\n")


if __name__ == "__main__":
    main() 