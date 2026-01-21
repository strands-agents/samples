#!/usr/bin/env python3
"""
# 🧠 Personal Agent

A specialized Strands agent that personalizes the answers based on websearch and memory.

## What This Example Shows

This example demonstrates:
- Creating a specialized Strands agent with memory capabilities
- Storing information across conversations and sessions
- Retrieving relevant memories based on context
- Using memory to create more personalized and contextual AI interactions

## Key Memory Operations

- **store**: Save important information for later retrieval
- **retrieve**: Access relevant memories based on queries
- **list**: View all stored memories

## Usage Examples

Storing memories: `Remember that I prefer tea over coffee`
Retrieving memories: `What do I prefer to drink?`
Listing all memories: `Show me everything you remember about me`
"""

import os

from ddgs import DDGS
from ddgs.exceptions import DDGSException, RatelimitException
from strands import Agent, tool
from strands_tools import http_request, mem0_memory

# Set up environment variables for AWS credentials and OpenSearch

# Define AWS credentials:
# os.environ["AWS_REGION"] = "<your-region>" # Replace with your region name e.g. 'us-west-2'
# os.environ['AWS_ACCESS_KEY_ID'] = "<your-aws-access-key-id>"
# os.environ['AWS_SECRET_ACCESS_KEY'] = "<your-aws-secret-access-key>"

# Make sure you have the Opensearch host setup:
# If not sure, run `sh prereqs/deploy_OSS.sh` to deploy OpenSearch Service in your CLI.
# If you manually created an Opensearch Collection, setup the environment variable here:
# os.environ["OPENSEARCH_HOST"] = "<your-opensearch-hostname>.<your-region>.aoss.amazonaws.com"


# User identifier
USER_ID = "new_user"  # In the real app, this would be set based on user authentication.

# System prompt
SYSTEM_PROMPT = """You are a helpful personal assistant that provides personalized responses based on user history.

Capabilities:
- Store information with mem0_memory (action="store")
- Retrieve memories with mem0_memory (action="retrieve")
- Search the web with duckduckgo_search

Key Rules:
- Be conversational and natural
- Retrieve memories before responding
- Store new user information and preferences
- Share only relevant information
- Politely indicate when information is unavailable
"""


@tool
def websearch(keywords: str, region: str = "us-en", max_results: int = 5) -> str:
    """Search the web for updated information.

    Args:
        keywords (str): The search query keywords.
        region (str): The search region: wt-wt, us-en, uk-en, ru-ru, etc..
        max_results (int | None): The maximum number of results to return.
    Returns:
        List of dictionaries with search results.

    """
    try:
        results = DDGS().text(keywords, region=region, max_results=max_results)
        return results if results else "No results found."
    except RatelimitException:
        return "Rate limit reached. Please try again later."
    except DDGSException as e:
        return f"Search error: {e}"


# Initialize agent
memory_agent = Agent(
    system_prompt=SYSTEM_PROMPT,
    tools=[mem0_memory, websearch, http_request],
)

if __name__ == "__main__":
    """Run the personal agent interactive session."""
    print("\n🧠 Personal Agent 🧠\n")
    print("This agent uses memory and websearch capabilities in Strands Agents.")
    print("You can ask me to remember things, retrieve memories, or search the web.")

    # Initialize user memory
    memory_agent.tool.mem0_memory(
        action="store", content=f"The user's name is {USER_ID}.", user_id=USER_ID
    )

    # Interactive loop
    while True:
        try:
            print(
                "\nWrite your question below or 'exit' to quit, or 'memory' to list all memories:"
            )
            user_input = input("\n> ").strip().lower()

            if user_input.lower() == "exit":
                print("\nGoodbye! 👋")
                break
            if user_input.lower() == "memory":
                all_memories = memory_agent.tool.mem0_memory(
                    action="list",
                    user_id=USER_ID,
                )
                continue
            else:
                memory_agent(user_input)

        except KeyboardInterrupt:
            print("\n\nExecution interrupted. Exiting...")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            print("Please try a different request.")
