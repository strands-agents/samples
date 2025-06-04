import re
from datetime import datetime
from typing import Dict, List, Optional


def format_search_results_for_agent(tavily_result: Dict) -> str:
    """
    Format Tavily search results into a well-structured string for language models.

    Args:
        tavily_result (Dict): A Tavily search result dictionary

    Returns:
        str: A formatted string with search results organized for easy consumption by LLMs
    """
    if (
        not tavily_result
        or "results" not in tavily_result
        or not tavily_result["results"]
    ):
        return "No search results found."

    formatted_results = []

    for i, doc in enumerate(tavily_result["results"], 1):
        # Extract metadata
        title = doc.get("title", "No title")
        url = doc.get("url", "No URL")

        # Create a formatted entry
        formatted_doc = f"\nRESULT {i}:\n"
        formatted_doc += f"Title: {title}\n"
        formatted_doc += f"URL: {url}\n"

        raw_content = doc.get("raw_content")

        # Prefer raw_content if it's available and not just whitespace
        if raw_content and raw_content.strip():
            formatted_doc += f"Raw Content: {raw_content.strip()}\n"
        else:
            # Fallback to content if raw_content is not suitable or not available
            content = doc.get("content", "").strip()
            formatted_doc += f"Content: {content}\n"

        formatted_results.append(formatted_doc)

    # Join all formatted results with a separator
    return "\n" + "\n".join(formatted_results)


def generate_filename(research_dir: str, question: str) -> str:
    """Generate a safe filename with timestamp based on the question."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_question = re.sub(r"[^\w\s-]", "", question[:40]).strip().lower()
    safe_question = re.sub(r"[-\s]+", "_", safe_question)
    return f"{research_dir}/{timestamp}_{safe_question}.md"


def format_crawl_results_for_agent(tavily_result: List[Dict]) -> str:
    """
    Format Tavily crawl results into a well-structured string for language models.

    Args:
        tavily_result (List[Dict]): A list of Tavily crawl result dictionaries

    Returns:
        str: The formatted crawl results
    """
    if not tavily_result:
        return "No crawl results found."

    formatted_results = []

    for i, doc in enumerate(tavily_result, 1):
        # Extract metadata
        url = doc.get("url", "No URL")
        raw_content = doc.get("raw_content", "")

        # Create a formatted entry
        formatted_doc = f"\nRESULT {i}:\n"
        formatted_doc += f"URL: {url}\n"

        if raw_content:
            # Extract a title from the first line if available
            title_line = raw_content.split("\n")[0] if raw_content else "No title"
            formatted_doc += f"Title: {title_line}\n"
            formatted_doc += (
                f"Content: {raw_content[:4000]}...\n"
                if len(raw_content) > 4000
                else f"Content: {raw_content}\n"
            )

        formatted_results.append(formatted_doc)

    # Join all formatted results with a separator
    return "\n" + "-" * 40 + "\n".join(formatted_results)
