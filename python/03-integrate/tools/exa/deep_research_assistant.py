#!/usr/bin/env python3
"""
Deep Research Assistant - Exa Tool Showcase Sample

A conversational AI agent that demonstrates the full power of Exa's search and
content extraction capabilities through a practical research workflow.

Exa Capabilities Demonstrated:
- Auto mode: Intelligent hybrid of neural + keyword search
- Category filtering: news, pdf, github for specialized searches
- Date filtering: Time-bound searches for recent content
- AI summaries: Automatic key insights extraction
- Structured output: JSON schema for structured summary extraction
- Subpage crawling: Discover related pages (citations, methodology)
- Subpage targeting: Keywords to find specific subpages (references, bibliography)
- Live crawling: Fresh content retrieval, bypassing cache
- Content extraction: Full text with character limit control

Research Workflow:
  1. Overview Search (Auto Mode) - General topic understanding
  2. News Search (Category: news) - Recent developments with date filtering
  3. Academic Papers (Category: pdf) - Technical depth from research
  4. Code & Projects (Category: github) - Practical implementations
  5. Deep Dive (exa_get_contents) - Detailed extraction from key sources
  6. Synthesis - Structured research brief with citations

Prerequisites:
    - AWS credentials configured for Bedrock access
    - EXA_API_KEY environment variable (https://dashboard.exa.ai/api-keys)

Usage:
    python deep_research_assistant.py
    python deep_research_assistant.py "Your research question here"
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from strands import Agent
from strands.models.bedrock import BedrockModel
from strands_tools.exa import exa_search, exa_get_contents


def load_system_prompt() -> str:
    """Load system prompt from .prompt file."""
    prompt_file = Path(__file__).parent / ".prompt"
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")
    raise FileNotFoundError(f"System prompt file not found: {prompt_file}")


def create_research_agent() -> Agent:
    """Create the Deep Research Agent with Bedrock model and Exa tools."""
    model = BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        region_name="us-west-2",
        max_tokens=16384,
    )

    return Agent(
        model=model,
        system_prompt=load_system_prompt(),
        tools=[exa_search, exa_get_contents],
    )


def run_research(agent: Agent, query: str) -> str:
    """Execute a comprehensive research workflow using Exa tools."""
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00.000Z")

    prompt = f"""
Research Question: "{query}"

Please conduct thorough research on this topic by executing ALL search steps
as specified in your instructions.

For Step 2 (News Search), use this date for start_published_date: 
"{thirty_days_ago}"

IMPORTANT REMINDERS:
1. Execute ALL 5 search steps - do not skip any
2. Use the EXACT parameters specified for each step
3. After all searches complete, provide a comprehensive research brief
4. Include ALL source URLs organized by category

Begin the research workflow now.
"""

    response = agent(prompt)
    return str(response)


def interactive_mode(agent: Agent):
    """Run the assistant in interactive mode for multiple queries."""
    print("\nInteractive Mode - Enter your research questions.")
    print("Type 'quit' or 'exit' to end the session.\n")

    while True:
        try:
            query = input("Research Query: ").strip()

            if not query:
                continue

            if query.lower() in ['quit', 'exit', 'bye', 'q']:
                print("Goodbye!")
                break

            run_research(agent, query)
            print("\n--- Research Complete ---\n")

        except KeyboardInterrupt:
            print("\nSession interrupted. Goodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break


def main():
    """Main entry point for the Deep Research Assistant."""
    print("Deep Research Assistant")
    print("=======================")
    print("Demonstrating Exa capabilities: auto mode, category filters, date filtering,")
    print("AI summaries, structured output (JSON schema), subpage crawling/targeting, and live crawling.\n")

    agent = create_research_agent()

    # Check for command-line query
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        run_research(agent, query)
    else:
        print("Options:")
        print("  1. Run demo query (battery technology for EVs)")
        print("  2. Enter interactive mode")

        try:
            choice = input("\nEnter choice (1/2): ").strip()

            if choice == "1":
                demo_query = "What are the latest advances in battery technology for electric vehicles?"
                run_research(agent, demo_query)
            elif choice == "2":
                interactive_mode(agent)
            else:
                print("Running demo query...")
                demo_query = "What are the latest advances in battery technology for electric vehicles?"
                run_research(agent, demo_query)

        except KeyboardInterrupt:
            print("\nGoodbye!")
        except EOFError:
            print("\nGoodbye!")


if __name__ == "__main__":
    main()
