#This sample application is intended solely for educational and knowledge-sharing purposes. It is not designed to provide investment guidance or financial advice.
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# Adapted from https://github.com/RamXX/mcp-tavily
# SPDX-License-Identifier: MIT

import json
import logging
import os
import sys
import yaml
from typing import List, Literal, Optional
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator
from tavily import InvalidAPIKeyError, TavilyClient, UsageLimitExceededError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s:%(lineno)d | %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("tavily_mcp")

# Load configuration
def load_config():
    """Load configuration from prereqs_config.yaml"""
    config_path = Path(__file__).parent / "prerequisites" / "prereqs_config.yaml"
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"⚠️ Could not load config: {e}")
        return {}

config = load_config()

# Load environment variables from .env.example file as fallback
env_path = Path(__file__).parent.parent / ".env.example"
load_dotenv(dotenv_path=env_path)

# Validate required configuration
def validate_config(config: dict) -> None:
    """Validate that required configuration values are present"""
    # Try config first, then environment variable
    tavily_api_key = (config.get("tavily_api_key") or os.getenv("TAVILY_API_KEY") or "").strip()
    
    if not tavily_api_key:
        error_msg = (
            f"\n{'='*80}\n"
            f"❌ ERROR: Missing required Tavily API key\n\n"
            f"📋 Action Required:\n"
            f"   Please add your Tavily API key to either:\n"
            f"   .env.example file (TAVILY_API_KEY)\n"
            f"{'='*80}\n"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    return tavily_api_key

# Validate configuration and get API key
api_key = validate_config(config)

try:
    mcp = FastMCP(
        name="tavily_tools",
    )
    logger.info("✅ Tavily MCP server initialized successfully")
except Exception as e:
    err_msg = f"Error: {str(e)}"
    logger.error(f"{err_msg}")

# Initialize Tavily client
client = TavilyClient(api_key=api_key)


# Base model for search parameters
class SearchBase(BaseModel):
    """Base parameters for Tavily search."""

    query: str = Field(description="Search query")
    max_results: int = Field(
        default=5,
        description="Maximum number of results to return",
        gt=0,
        lt=20,
    )
    include_domains: Optional[List[str]] = Field(
        default=None,
        description="List of domains to specifically include in the search results (e.g. ['example.com', 'test.org'] or 'example.com')",
    )
    exclude_domains: Optional[List[str]] = Field(
        default=None,
        description="List of domains to specifically exclude from the search results (e.g. ['example.com', 'test.org'] or 'example.com')",
    )

    @field_validator("include_domains", "exclude_domains", mode="before")
    @classmethod
    def parse_domains_list(cls, v):
        """Parse domain lists from various input formats."""
        if v is None:
            return []
        if isinstance(v, list):
            return [domain.strip() for domain in v if domain.strip()]
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            try:
                # Try to parse as JSON string
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [domain.strip() for domain in parsed if domain.strip()]
                return [parsed.strip()]  # Single value from JSON
            except json.JSONDecodeError:
                # Not JSON, check if comma-separated
                if "," in v:
                    return [domain.strip() for domain in v.split(",") if domain.strip()]
                return [v]  # Single domain
        return []


def format_results(response: dict) -> str:
    """Format Tavily search results into a readable string."""
    output = []

    # Add domain filter information if present
    if response.get("included_domains") or response.get("excluded_domains"):
        filters = []
        if response.get("included_domains"):
            filters.append(
                f"Including domains: {', '.join(response['included_domains'])}"
            )
        if response.get("excluded_domains"):
            filters.append(
                f"Excluding domains: {', '.join(response['excluded_domains'])}"
            )
        output.append("Search Filters:")
        output.extend(filters)
        output.append("")  # Empty line for separation

    if response.get("answer"):
        output.append(f"Answer: {response['answer']}")
        output.append("\nSources:")
        # Add immediate source references for the answer
        for result in response["results"]:
            output.append(f"- {result['title']}: {result['url']}")
        output.append("")  # Empty line for separation

    output.append("Detailed Results:")
    for result in response["results"]:
        output.append(f"\nTitle: {result['title']}")
        output.append(f"URL: {result['url']}")
        output.append(f"Content: {result['content']}")
        if result.get("published_date"):
            output.append(f"Published: {result['published_date']}")

    return "\n".join(output)


@mcp.tool()
async def tavily_web_search(
    query: str,
    max_results: int = 5,
    search_depth: Literal["basic", "advanced"] = "basic",
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
) -> str:
    """Performs a comprehensive web search using Tavily's AI-powered search engine.
    Excels at extracting and summarizing relevant content from web pages, making it ideal for research,
    fact-finding, and gathering detailed information.

    Args:
        query: Search query
        max_results: Maximum number of results to return (default: 5)
        search_depth: Depth of search - 'basic' or 'advanced' (default: basic)
        include_domains: List of domains to specifically include in results (optional)
        exclude_domains: List of domains to specifically exclude from results (optional)

    Returns:
        Formatted search results text
    """
    try:
        # Parse domain lists
        include_domains_list = (
            SearchBase.parse_domains_list(include_domains) if include_domains else []
        )
        exclude_domains_list = (
            SearchBase.parse_domains_list(exclude_domains) if exclude_domains else []
        )

        response = client.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_domains=include_domains_list,
            exclude_domains=exclude_domains_list,
        )

        # Add domain filter information to response for formatting
        if include_domains_list:
            response["included_domains"] = include_domains_list
        if exclude_domains_list:
            response["excluded_domains"] = exclude_domains_list

        return format_results(response)
    except (InvalidAPIKeyError, UsageLimitExceededError) as e:
        error_msg = f"Tavily API error: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"tavily_web_search error: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
async def tavily_answer_search(
    query: str,
    max_results: int = 5,
    search_depth: Literal["basic", "advanced"] = "advanced",
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
) -> str:
    """Performs a web search using Tavily's AI search engine and generates a direct answer to the query,
    along with supporting search results.

    Args:
        query: Search query
        max_results: Maximum number of results to return (default: 5)
        search_depth: Depth of search - 'basic' or 'advanced' (default: advanced)
        include_domains: List of domains to specifically include in results (optional)
        exclude_domains: List of domains to specifically exclude from results (optional)

    Returns:
        Formatted search results text with answer
    """
    try:
        # Parse domain lists
        include_domains_list = (
            SearchBase.parse_domains_list(include_domains) if include_domains else []
        )
        exclude_domains_list = (
            SearchBase.parse_domains_list(exclude_domains) if exclude_domains else []
        )

        response = client.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_answer=True,
            include_domains=include_domains_list,
            exclude_domains=exclude_domains_list,
        )

        # Add domain filter information to response for formatting
        if include_domains_list:
            response["included_domains"] = include_domains_list
        if exclude_domains_list:
            response["excluded_domains"] = exclude_domains_list

        return format_results(response)
    except (InvalidAPIKeyError, UsageLimitExceededError) as e:
        error_msg = f"Tavily API error: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"tavily_answer_search error: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
async def tavily_news_search(
    query: str,
    max_results: int = 5,
    days: Optional[int] = 3,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
) -> str:
    """Searches recent news articles using Tavily's specialized news search functionality.

    Args:
        query: Search query
        max_results: Maximum number of results to return (default: 5)
        days: Number of days back to search (default: 3)
        include_domains: List of domains to specifically include in results (optional)
        exclude_domains: List of domains to specifically exclude from results (optional)

    Returns:
        Formatted news search results text
    """
    try:
        # Parse domain lists
        include_domains_list = (
            SearchBase.parse_domains_list(include_domains) if include_domains else []
        )
        exclude_domains_list = (
            SearchBase.parse_domains_list(exclude_domains) if exclude_domains else []
        )

        response = client.search(
            query=query,
            max_results=max_results,
            topic="news",
            days=days,
            include_domains=include_domains_list,
            exclude_domains=exclude_domains_list,
        )

        # Add domain filter information to response for formatting
        if include_domains_list:
            response["included_domains"] = include_domains_list
        if exclude_domains_list:
            response["excluded_domains"] = exclude_domains_list

        return format_results(response)
    except (InvalidAPIKeyError, UsageLimitExceededError) as e:
        error_msg = f"Tavily API error: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"tavily_news_search error: {str(e)}"
        logger.error(error_msg)
        return error_msg


if __name__ == "__main__":
    mcp.run()
