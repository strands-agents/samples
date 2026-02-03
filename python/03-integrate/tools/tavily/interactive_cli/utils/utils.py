import re
from datetime import datetime
from typing import Dict, List


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
        formatted_results (str): The formatted crawl results
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


def format_extract_results_for_agent(tavily_result):
    """
    Format Tavily extract results into a well-structured string for language models.

    Args:
        tavily_result (Dict): A Tavily extract result dictionary

    Returns:
        str: A formatted string with extract results organized for easy consumption by LLMs
    """
    if not tavily_result or "results" not in tavily_result:
        return "No extract results found."

    formatted_results = []

    # Process successful results
    results = tavily_result.get("results", [])
    for i, doc in enumerate(results, 1):
        url = doc.get("url", "No URL")
        raw_content = doc.get("raw_content", "")
        images = doc.get("images", [])

        formatted_doc = f"\nEXTRACT RESULT {i}:\n"
        formatted_doc += f"URL: {url}\n"

        if raw_content:
            # Truncate very long content for readability
            if len(raw_content) > 5000:
                formatted_doc += f"Content: {raw_content[:5000]}...\n"
            else:
                formatted_doc += f"Content: {raw_content}\n"
        else:
            formatted_doc += "Content: No content extracted\n"

        if images:
            formatted_doc += f"Images found: {len(images)} images\n"
            for j, image_url in enumerate(images[:3], 1):  # Show up to 3 images
                formatted_doc += f"  Image {j}: {image_url}\n"
            if len(images) > 3:
                formatted_doc += f"  ... and {len(images) - 3} more images\n"

        formatted_results.append(formatted_doc)

    # Process failed results if any
    failed_results = tavily_result.get("failed_results", [])
    if failed_results:
        formatted_results.append("\nFAILED EXTRACTIONS:\n")
        for i, failure in enumerate(failed_results, 1):
            url = failure.get("url", "Unknown URL")
            error = failure.get("error", "Unknown error")
            formatted_results.append(f"Failed {i}: {url} - {error}\n")

    # Add response time info
    response_time = tavily_result.get("response_time", 0)
    formatted_results.append(f"\nResponse time: {response_time} seconds")

    return "\n" + "".join(formatted_results)
