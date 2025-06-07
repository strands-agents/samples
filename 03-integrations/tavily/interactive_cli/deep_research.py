import os
from typing import Optional

from dotenv import load_dotenv
from strands import Agent, tool
from strands.models import BedrockModel
from tavily import TavilyClient
from utils.prompts import RESEARCH_FORMATTER_PROMPT, SYSTEM_PROMPT
from utils.utils import (
    format_crawl_results_for_agent,
    format_extract_results_for_agent,
    format_search_results_for_agent,
    generate_filename,
)

# Define constants
RESEARCH_DIR = "research_findings"

load_dotenv()
# OR define it here
# os.environ["TAVILY_API_KEY"] = "<YOUR_TAVILY_API_KEY>"

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
    This tool conducts thorough web searches. The results will be ranked by semantic relevance and include title, url, and content.

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
def web_extract(
    urls: str | list[str], include_images: bool = False, extract_depth: str = "basic"
) -> str:
    """Extract content from one or more web pages using Tavily's extract API.

    Args:
        urls (str | list[str]): A single URL string or a list of URLs to extract content from.
        include_images (bool, optional): Whether to also extract image URLs from the pages.
                                       Defaults to False.
        extract_depth (str, optional): The depth of extraction. 'basic' provides standard
                                     content extraction, 'advanced' provides more detailed
                                     extraction. Defaults to "basic".

    Returns:
        str: A formatted string containing the extracted content from each URL, including
             the full raw content, any images found (if requested), and information about
             any URLs that failed to be processed.
    """
    try:
        # Ensure urls is always a list for the API call
        if isinstance(urls, str):
            urls_list = [urls]
        else:
            urls_list = urls

        # Clean and validate URLs
        cleaned_urls = []
        for url in urls_list:
            if url.strip().startswith("{") and '"url":' in url:
                import re

                m = re.search(r'"url"\s*:\s*"([^"]+)"', url)
                if m:
                    url = m.group(1)

            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            cleaned_urls.append(url)

        # Call Tavily extract API
        api_response = tavily_client.extract(
            urls=cleaned_urls,  # List of URLs to extract content from
            include_images=include_images,  # Whether to include image extraction
            extract_depth=extract_depth,  # Depth of extraction (basic or advanced)
        )

        # Format the results for the agent
        formatted_results = format_extract_results_for_agent(api_response)
        return formatted_results

    except Exception as e:
        return f"Error during extraction: {e}\nURLs attempted: {urls}\nFailed to extract content."


@tool
def format_research_response(
    research_content: str,
    format_style: Optional[str] = None,
    user_query: Optional[str] = None,
) -> str:
    """Format research content into a well-structured, properly cited response.
    The response will clearly address the user's query and present the research results in markdown format.

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
    This tool conducts deep web crawls that find all nested links from a single page.
    This is great for finding all the information that is linked from a specific webpage.

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
    This tool is helpful for complex or long research, to write it to a markdown file.

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


@tool
def read_file(filepath: str) -> str:
    """Read the contents of a file. This tool accesses the contents of a specific file when
    you need to understand or update parts of a particular file or files.

    Args:
        filepath (str): The path to the file to read

    Returns:
        str: The contents of the file as a string, or an error message if the file cannot be read
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return f"Error: File not found at path '{filepath}'"
    except Exception as e:
        return f"Error reading file: {str(e)}"


web_agent = Agent(
    system_prompt=SYSTEM_PROMPT,
    tools=[
        web_search,
        web_crawl,
        web_extract,
        format_research_response,
        read_file,
        write_markdown_file,
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
        "Type your question / follow up question or 'exit' to quit.\n"
    )
    print(
        "Try following examples: ",
        "- What are the latest developments in quantum computing?\n"
        "- Find recent studies on climate change from 2022–2023, focusing on impact to coastal regions.\n",
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
