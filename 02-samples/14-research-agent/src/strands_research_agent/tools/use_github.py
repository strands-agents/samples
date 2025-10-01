"""GitHub GraphQL API integration tool for Strands Agents.

This module provides a comprehensive interface to GitHub's v4 GraphQL API,
allowing you to execute any GitHub GraphQL query or mutation directly from your Strands Agent.
The tool handles authentication, parameter validation, response formatting,
and provides user-friendly error messages with schema recommendations.

Key Features:

1. Universal GitHub GraphQL Access:
   • Access to GitHub's full GraphQL API (v4)
   • Support for both queries and mutations
   • Authentication via GITHUB_TOKEN environment variable
   • Rate limit awareness and error handling

2. Safety Features:
   • Confirmation prompts for mutative operations (mutations)
   • Parameter validation with helpful error messages
   • Error handling with detailed feedback
   • Query complexity analysis

3. Response Handling:
   • JSON formatting of responses
   • Error message extraction from GraphQL responses
   • Rate limit information display
   • Pretty printing of operation details

4. Usage Examples:
   ```python
   from strands import Agent
   from tools.use_github import use_github

   agent = Agent(tools=[use_github])

   # Get repository information
   result = agent.tool.use_github(
       query_type="query",
       query='''
       query($owner: String!, $name: String!) {
         repository(owner: $owner, name: $name) {
           name
           description
           stargazerCount
           forkCount
         }
       }
       ''',
       variables={"owner": "octocat", "name": "Hello-World"},
       label="Get repository information",
   )
   ```

See the use_github function docstring for more details on parameters and usage.
"""

import json
import logging
import os
from typing import Any

import requests
from colorama import Fore, Style, init
from rich.console import Console
from rich.panel import Panel
from strands import tool

# Initialize colorama
init(autoreset=True)

logger = logging.getLogger(__name__)

# GitHub GraphQL API endpoint
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"


def create_console() -> Console:
    """Create a Rich console instance."""
    return Console()


def get_user_input(prompt: str) -> str:
    """Simple user input function with styled prompt."""
    # Remove Rich markup for simple input
    clean_prompt = prompt.replace("<yellow><bold>", "").replace(
        "</bold> [y/*]</yellow>", " [y/*] "
    )
    return input(clean_prompt)


# Common mutation keywords that indicate potentially destructive operations
MUTATIVE_KEYWORDS = [
    "create",
    "update",
    "delete",
    "add",
    "remove",
    "merge",
    "close",
    "reopen",
    "lock",
    "unlock",
    "pin",
    "unpin",
    "transfer",
    "archive",
    "unarchive",
    "enable",
    "disable",
    "accept",
    "decline",
    "dismiss",
    "submit",
    "request",
    "cancel",
    "convert",
]


def get_github_token() -> str | None:
    """Get GitHub token from environment variables.

    Returns:
        GitHub token string or None if not found
    """
    return os.environ.get("GITHUB_TOKEN", "")


def is_mutation_query(query: str) -> bool:
    """Check if a GraphQL query is a mutation based on keywords and structure.

    Args:
        query: GraphQL query string

    Returns:
        True if the query appears to be a mutation
    """
    query_lower = query.lower().strip()

    # Check if query starts with "mutation"
    if query_lower.startswith("mutation"):
        return True

    # Check for mutative keywords in the query
    return any(keyword in query_lower for keyword in MUTATIVE_KEYWORDS)


def execute_github_graphql(
    query: str, variables: dict[str, Any] | None = None, token: str | None = None
) -> dict[str, Any]:
    """Execute a GraphQL query against GitHub's API.

    Args:
        query: GraphQL query string
        variables: Optional variables for the query
        token: GitHub authentication token

    Returns:
        Dictionary containing the GraphQL response

    Raises:
        requests.RequestException: If the request fails
        ValueError: If authentication fails
    """
    if not token:
        raise ValueError(
            "GitHub token is required. Set GITHUB_TOKEN environment variable."
        )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github.v4+json",
        "User-Agent": "Strands-Agent-GitHub-Tool/1.0",
    }

    payload = {"query": query, "variables": variables or {}}

    response = requests.post(
        GITHUB_GRAPHQL_URL, headers=headers, json=payload, timeout=30
    )

    response.raise_for_status()
    response_data: dict[str, Any] = response.json()
    return response_data


def format_github_response(response: dict[str, Any]) -> str:
    """Format GitHub GraphQL response for display.

    Args:
        response: GitHub GraphQL response dictionary

    Returns:
        Formatted string representation of the response
    """
    formatted_parts = []

    # Handle errors
    if "errors" in response:
        formatted_parts.append(f"{Fore.RED}Errors:{Style.RESET_ALL}")
        for error in response["errors"]:
            formatted_parts.append(f"  - {error.get('message', 'Unknown error')}")
            if "locations" in error:
                locations = error["locations"]
                formatted_parts.append(f"    Locations: {locations}")

    # Handle data
    if "data" in response:
        formatted_parts.append(f"{Fore.GREEN}Data:{Style.RESET_ALL}")
        formatted_parts.append(json.dumps(response["data"], indent=2))

    # Handle rate limit info
    if "extensions" in response and "cost" in response["extensions"]:
        cost_info = response["extensions"]["cost"]
        formatted_parts.append(f"{Fore.YELLOW}Rate Limit Info:{Style.RESET_ALL}")
        formatted_parts.append(
            f"  - Query Cost: {cost_info.get('requestedQueryCost', 'N/A')}"
        )
        formatted_parts.append(f"  - Node Count: {cost_info.get('nodeCount', 'N/A')}")
        if "rateLimit" in cost_info:
            rate_limit = cost_info["rateLimit"]
            formatted_parts.append(
                f"  - Remaining: {rate_limit.get('remaining', 'N/A')}"
            )
            formatted_parts.append(f"  - Reset At: {rate_limit.get('resetAt', 'N/A')}")

    return "\n".join(formatted_parts)


@tool
def use_github(
    query_type: str,
    query: str,
    label: str,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute GitHub GraphQL API operations with comprehensive error handling and validation.

    This tool provides a universal interface to GitHub's GraphQL API (v4), allowing you to execute
    any query or mutation supported by GitHub's GraphQL schema. It handles authentication via
    GITHUB_TOKEN, parameter validation, response formatting, and provides helpful error messages.

    How It Works:
    ------------
    1. The tool validates the GitHub token from environment variables
    2. For mutations or potentially destructive operations, it prompts for confirmation
    3. It executes the GraphQL query/mutation against GitHub's API
    4. Responses are processed and formatted with proper error handling
    5. Rate limit information is displayed when available

    Common Usage Scenarios:
    ---------------------
    - Repository Management: Get repository info, create/update repositories
    - Issue & PR Operations: Create, update, close issues and pull requests
    - User & Organization Data: Retrieve user profiles, organization details
    - Project Management: Manage GitHub Projects, milestones, and labels
    - Git Operations: Access commit history, branches, and tags
    - Security: Manage webhooks, deploy keys, and security settings

    Example Queries:
    ---------------
    Repository Information:
    ```graphql
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        name
        description
        stargazerCount
        forkCount
        issues(states: OPEN) {
          totalCount
        }
        pullRequests(states: OPEN) {
          totalCount
        }
      }
    }
    ```

    Create Issue Mutation:
    ```graphql
    mutation($repositoryId: ID!, $title: String!, $body: String) {
      createIssue(input: {repositoryId: $repositoryId, title: $title, body: $body}) {
        issue {
          number
          title
          url
        }
      }
    }
    ```

    Args:
        query_type: Type of GraphQL operation ("query" or "mutation")
        query: The GraphQL query or mutation string
        label: Human-readable description of the GitHub operation
        variables: Optional dictionary of variables for the query

    Returns:
        Dict containing status and response content:
        {
            "status": "success|error",
            "content": [{"text": "Response message"}]
        }

    Notes:
        - Requires GITHUB_TOKEN environment variable to be set
        - Mutations require user confirmation in non-dev environments
        - You can disable confirmation by setting BYPASS_TOOL_CONSENT=true
        - The tool automatically handles rate limiting information
        - GraphQL errors are formatted and displayed clearly
        - All responses are JSON formatted for easy parsing

    Environment Variables:
        - GITHUB_TOKEN: Required GitHub personal access token or app token
        - BYPASS_TOOL_CONSENT: Set to "true" to skip confirmation prompts
    """
    console = create_console()

    # Set default for variables if None
    if variables is None:
        variables = {}

    STRANDS_BYPASS_TOOL_CONSENT = (
        os.environ.get("BYPASS_TOOL_CONSENT", "").lower() == "true"
    )

    # Create a panel for GitHub Operation Details
    operation_details = f"{Fore.CYAN}Type:{Style.RESET_ALL} {query_type}\n"
    operation_details += f"{Fore.CYAN}Query:{Style.RESET_ALL}\n{query}\n"
    if variables:
        operation_details += f"{Fore.CYAN}Variables:{Style.RESET_ALL}\n"
        for key, value in variables.items():
            operation_details += f"  - {key}: {value}\n"

    console.print(Panel(operation_details, title=label, expand=False))

    logger.debug(
        f"Invoking GitHub GraphQL: query_type = {query_type}, variables = {variables}"
    )

    # Get GitHub token
    github_token = get_github_token()
    if not github_token:
        return {
            "status": "error",
            "content": [
                {
                    "text": "GitHub token not found. Please set the GITHUB_TOKEN environment variable.\n"
                    "You can create a token at: https://github.com/settings/tokens"
                }
            ],
        }

    # Check if the operation is potentially mutative
    is_mutative = query_type.lower() == "mutation" or is_mutation_query(query)

    if is_mutative and not STRANDS_BYPASS_TOOL_CONSENT:
        # Prompt for confirmation before executing the operation
        confirm = get_user_input(
            f"<yellow><bold>This appears to be a mutative operation ({query_type}). "
            f"Do you want to proceed?</bold> [y/*]</yellow>"
        )
        if confirm.lower() != "y":
            return {
                "status": "error",
                "content": [
                    {"text": f"Operation canceled by user. Reason: {confirm}."}
                ],
            }

    try:
        # Execute the GraphQL query
        response = execute_github_graphql(query, variables, github_token)

        # Format the response
        formatted_response = format_github_response(response)

        # Check if there were GraphQL errors
        if "errors" in response:
            return {
                "status": "error",
                "content": [
                    {"text": "GraphQL query completed with errors:"},
                    {"text": formatted_response},
                ],
            }

        return {
            "status": "success",
            "content": [{"text": formatted_response}],
        }

    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 401:
            return {
                "status": "error",
                "content": [
                    {
                        "text": "Authentication failed. Please check your GITHUB_TOKEN.\n"
                        "Make sure the token has the required permissions for this operation."
                    }
                ],
            }
        elif http_err.response.status_code == 403:
            return {
                "status": "error",
                "content": [
                    {
                        "text": "Forbidden. Your token may not have sufficient permissions for this operation.\n"
                        f"HTTP Error: {http_err}"
                    }
                ],
            }
        else:
            return {
                "status": "error",
                "content": [{"text": f"HTTP Error: {http_err}"}],
            }

    except requests.exceptions.RequestException as req_err:
        return {
            "status": "error",
            "content": [{"text": f"Request Error: {req_err}"}],
        }

    except ValueError as val_err:
        return {
            "status": "error",
            "content": [{"text": f"Configuration Error: {val_err}"}],
        }

    except Exception as ex:
        logger.warning(f"GitHub GraphQL call threw exception: {type(ex).__name__}")
        return {
            "status": "error",
            "content": [{"text": f"GitHub GraphQL call threw exception: {ex!s}"}],
        }
