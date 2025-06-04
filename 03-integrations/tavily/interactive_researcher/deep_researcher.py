import logging
import os
from typing import Optional

from dotenv import load_dotenv
from strands import Agent, tool
from strands.models import BedrockModel
from tavily import TavilyClient
from utils.prompts import RESEARCH_FORMATTER_PROMPT, SYSTEM_PROMPT
from utils.utils import (format_crawl_results_for_agent,
                         format_search_results_for_agent, generate_filename)

# Enables Strands debug log level
logging.getLogger("strands").setLevel(logging.DEBUG)  # or logging.INFO
# Sets the logging format and streams logs to stderr
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

# Define constants
RESEARCH_DIR = "research_findings"

load_dotenv()
# OR define it here
# os.environ["TAVILY_API_KEY"] = "<>YOUR_TAVILY_API_KEY>"

if not os.getenv("TAVILY_API_KEY"):
    raise ValueError(
        "TAVILY_API_KEY environment variable is not set. Please add it to your .env file."
    )

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@tool
def web_search(
    query: str,
    max_results: Optional[int] = 10,
    time_range: Optional[str] = None,
    include_domains: Optional[str] = None,
) -> str:
    """Perform a web search. Returns the search results as a string, with the title, url, and content of each result ranked by relevance.

    Args:
        query (str): The search query to be sent for the web search.
        max_results (Optional[int]): The maximum number of search results to return. For simple queries, 5 is recommended, for complex queries, 10 is recommended.
        time_range (Optional[str]): Limits results to content published within a specific timeframe.
            Valid values: 'd' (day - 24h), 'w' (week - 7d), 'm' (month - 30d), 'y' (year - 365d).
            Defaults to None.
        include_domains (Optional[str]): A list of domains to restrict search results to.
            Only results from these domains will be returned. Defaults to None.

    Returns:
        str: The formatted web search results
    """
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    formatted_results = format_search_results_for_agent(
        client.search(
            query=query,  # The search query to execute with Tavily.
            max_results=max_results,
            time_range=time_range,
            # list of domains to specifically include in the search results.
            include_domains=include_domains,
        )
    )
    return formatted_results


@tool
def format_research_response(
    research_content: str,
    format_style: Optional[str] = None,
    user_query: Optional[str] = None,
) -> str:
    """Format research content into a well-structured, properly cited response.

    This tool uses a specialized Research Formatter Agent to transform raw research
    into polished, reader-friendly content with proper citations and optimal structure.

    Args:
        research_content (str): The raw research content to be formatted
        format_style (Optional[str]): Desired format style (e.g., "blog", "report",
                                    "executive summary", "bullet points", "direct answer")
        user_query (Optional[str]): Original user question to help determine appropriate format

    Returns:
        str: Professionally formatted research response with proper citations,
             clear structure, and appropriate style for the intended audience
    """
    try:
        bedrock_model = BedrockModel(
            model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
            region_name="us-east-1",
        )
        # Strands Agents SDK makes it easy to create a specialized agent
        formatter_agent = Agent(
            model=bedrock_model,
            system_prompt=RESEARCH_FORMATTER_PROMPT,
        )

        # Prepare the input for the formatter
        format_input = f"Research Content:\n{research_content}\n\n"

        if format_style:
            format_input += f"Requested Format Style: {format_style}\n\n"

        if user_query:
            format_input += f"Original User Query: {user_query}\n\n"

        format_input += "Please format this research content according to the guidelines and appropriate style."

        # Call the agent and return its response
        response = formatter_agent(format_input)
        return str(response)
    except Exception as e:
        return f"Error in research formatting: {str(e)}"


@tool
def web_crawl(url: str, instructions: Optional[str] = None) -> str:
    """
    Crawls a given URL, processes the results, and formats them into a string.

    Args:
        url (str): The URL of the website to crawl.
        instructions (Optional[str]): Specific instructions to guide the
                                     Tavily crawler, such as focusing on
                                     certain types of content or avoiding
                                     others. Defaults to None.

    Returns:
        str: A formatted string containing the crawl results. Each result includes
             the URL and a snippet of the page content.
             If an error occurs during the crawl process (e.g., network issue,
             API error), a string detailing the error and the attempted URL is
             returned.
    """
    max_depth = 2
    limit = 20

    if url.strip().startswith("{") and '"url":' in url:
        import re

        m = re.search(r'"url"\s*:\s*"([^"]+)"', url)
        if m:
            url = m.group(1)

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        # Crawls the web using Tavily API
        api_response = tavily_client.crawl(
            url=url,  # The URL to crawl
            max_depth=max_depth,  # Defines how far from the base URL the crawler can explore
            limit=limit,  # Limits the number of results returned
            instructions=instructions,  # Optional instructions for the crawler
        )

        tavily_results = (
            api_response.get("results")
            if isinstance(api_response, dict)
            else api_response
        )

        formatted = format_crawl_results_for_agent(tavily_results)
        return formatted
    except Exception as e:
        return f"Error: {e}\n" f"URL attempted: {url}\n" "Failed to crawl the website."


@tool
def write_markdown_file(filename: str, content: str) -> str:
    """Write markdown content to a file.

    Args:
        filename (str): The name of the file to write to
        content (str): The markdown content to write

    Returns:
        str: A confirmation message
    """
    filename = generate_filename(RESEARCH_DIR, filename)
    print(f"Saving research findings to {filename}...")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Successfully saved research to {filename}"


web_agent = Agent(
    system_prompt=SYSTEM_PROMPT,
    tools=[
        web_search,
        web_crawl,
        write_markdown_file,
        format_research_response,
    ],
)


def run_interactive_session() -> None:
    """Run an interactive terminal session for research."""
    # Create research directory if it doesn't exist
    os.makedirs(RESEARCH_DIR, exist_ok=True)

    print("\n🌐 Web Researcher Agent 🌐\n")
    print("─" * 50)
    print(
        "This agent uses Tavily search API to help you research topics.\n"
        f"For complex research, results will be saved in the '{RESEARCH_DIR}' directory.\n"
        "Type your question or 'exit' to quit.\n"
    )
    print(
        "Try following examples: ",
        "- What are the latest developments in quantum computing?\n"
        "- Find recent studies on climate change from 2022–2023, focusing on impact to coastal regions.",
    )

    while True:
        query = input("\nResearch> ").strip()
        if query.lower() == "exit":
            print(f"\nUsage metrics:\n{web_agent.event_loop_metrics}")
            print("Goodbye! 👋")
            break

        if not query:
            continue

        print("\nResearching... Please wait.\n")
        response = web_agent(query)
        print(response)
        print("\n✅ Research complete! You may ask another question or type 'exit'.\n")


if __name__ == "__main__":
    run_interactive_session()
