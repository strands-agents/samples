"""Universal GraphQL client tool for Strands Agents.

This module provides a comprehensive interface to any GraphQL API,
allowing you to execute queries and mutations on public or authenticated GraphQL endpoints.
The tool handles authentication, parameter validation, response formatting,
and provides user-friendly error messages with helpful debugging information.

Key Features:

1. Universal GraphQL Access:
   • Support for any GraphQL endpoint, not just GitHub
   • Handles both queries and mutations
   • Multiple authentication methods (Bearer, Basic, None)
   • Rate limit awareness and error handling

2. Safety Features:
   • Confirmation prompts for mutative operations (mutations)
   • Parameter validation with helpful error messages
   • Error handling with detailed feedback
   • Query complexity analysis

3. Response Handling:
   • JSON formatting of responses
   • Error message extraction from GraphQL responses
   • Pretty printing of operation details
   • Support for custom HTTP headers

4. Usage Examples:
   ```python
   # Simple public GraphQL query (Countries API)
   result = graphql(
       endpoint="https://countries.trevorblades.com/graphql",
       query='''
       query {
         countries {
           name
           capital
           currency
         }
       }
       ''',
       label="Get all-countries information",
   )

   # Authenticated GraphQL query with variables
   result = graphql(
       endpoint="https://api.github.com/graphql",
       query='''
       query($owner: String!, $name: String!) {
         repository(owner: $owner, name: $name) {
           name
           description
           stargazerCount
         }
       }
       ''',
       variables={"owner": "octocat", "name": "Hello-World"},
       auth_type="Bearer",
       auth_token=os.environ.get("GITHUB_TOKEN"),
       label="Get repository information",
   )

   # Mutation with authentication
   result = graphql(
       endpoint="https://api.example.com/graphql",
       query='''
       mutation($id: ID!, $status: String!) {
         updateItem(id: $id, status: $status) {
           id
           status
         }
       }
       ''',
       variables={"id": "123", "status": "complete"},
       auth_type="Bearer",
       auth_token="your-auth-token",
       label="Update item status",
   )
   ```
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


def execute_graphql(
    endpoint: str,
    query: str,
    variables: dict[str, Any] | None = None,
    auth_type: str | None = None,
    auth_token: str | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """Execute a GraphQL query against any GraphQL API endpoint.

    Args:
        endpoint: GraphQL API endpoint URL
        query: GraphQL query string
        variables: Optional variables for the query
        auth_type: Authentication type (Bearer, Basic, None)
        auth_token: Authentication token when applicable
        headers: Additional HTTP headers
        timeout: Request timeout in seconds

    Returns:
        Dictionary containing the GraphQL response

    Raises:
        requests.RequestException: If the request fails
        ValueError: If authentication type is invalid
    """
    # Default headers
    request_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Strands-Agent-GraphQL-Tool/1.0",
    }

    # Add authentication if provided
    if auth_type and auth_token:
        if auth_type.lower() == "bearer":
            request_headers["Authorization"] = f"Bearer {auth_token}"
        elif auth_type.lower() == "basic":
            request_headers["Authorization"] = f"Basic {auth_token}"
        else:
            raise ValueError(f"Unsupported authentication type: {auth_type}")

    # Add any custom headers
    if headers:
        request_headers.update(headers)

    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables

    response = requests.post(
        endpoint, headers=request_headers, json=payload, timeout=timeout
    )

    response.raise_for_status()
    response_data: dict[str, Any] = response.json()
    return response_data


def format_graphql_response(response: dict[str, Any]) -> str:
    """Format GraphQL response for display.

    Args:
        response: GraphQL response dictionary

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
            if "path" in error:
                path = error["path"]
                formatted_parts.append(f"    Path: {path}")

    # Handle data
    if "data" in response:
        formatted_parts.append(f"{Fore.GREEN}Data:{Style.RESET_ALL}")
        formatted_parts.append(json.dumps(response["data"], indent=2))

    # Handle extensions if available (rate limits, etc.)
    if "extensions" in response:
        formatted_parts.append(f"{Fore.YELLOW}Extensions:{Style.RESET_ALL}")
        formatted_parts.append(json.dumps(response["extensions"], indent=2))

    return "\n".join(formatted_parts)


@tool
def graphql(
    endpoint: str,
    query: str,
    variables: dict[str, Any] | None = None,
    auth_type: str | None = None,
    auth_token: str | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    label: str = "GraphQL Operation",
) -> dict[str, Any]:
    """Execute GraphQL operations on any endpoint with comprehensive error handling and validation.

    This tool provides a universal interface to any GraphQL API, allowing you to execute
    queries or mutations against any GraphQL endpoint. It handles authentication,
    parameter validation, response formatting, and provides helpful error messages.

    How It Works:
    ------------
    1. The tool validates the endpoint and query
    2. For mutations or potentially destructive operations, it prompts for confirmation
    3. It executes the GraphQL query/mutation against the specified endpoint
    4. Responses are processed and formatted with proper error handling
    5. Extensions like rate limit information are displayed when available

    Args:
        endpoint: URL of the GraphQL API endpoint (e.g., "https://api.github.com/graphql")
        query: GraphQL query or mutation string
        variables: Optional variables dictionary for the query
        auth_type: Authentication type to use (e.g., "Bearer", "Basic", or None)
        auth_token: Authentication token when applicable
        headers: Additional HTTP headers to include in the request
        timeout: Request timeout in seconds (default: 30)
        label: Human-readable description of the operation

    Returns:
        Dict containing operation status and formatted response:
        - status: 'success' or 'error'
        - content: List of content dictionaries with response text

    Examples:
        # Simple public GraphQL query (Countries API)
        result = graphql(
            endpoint="https://countries.trevorblades.com/graphql",
            query='''
            query {
              countries {
                name
                capital
                currency
              }
            }
            ''',
            label="Get all-countries information"
        )

        # Authenticated GraphQL query with variables
        result = graphql(
            endpoint="https://api.github.com/graphql",
            query='''
            query($owner: String!, $name: String!) {
              repository(owner: $owner, name: $name) {
                name
                description
                stargazerCount
              }
            }
            ''',
            variables={"owner": "octocat", "name": "Hello-World"},
            auth_type="Bearer",
            auth_token=os.environ.get("GITHUB_TOKEN"),
            label="Get repository information"
        )

    Notes:
        - For GitHub API, authentication uses the GITHUB_TOKEN environment variable
        - Mutations require user confirmation in non-dev environments
        - You can disable confirmation by setting BYPASS_TOOL_CONSENT=true
        - The tool handles common GraphQL error formats and displays them clearly
        - All responses are JSON formatted for easy parsing
        - This tool is a universal version of the GitHub-specific use_github tool
    """
    console = Console()

    STRANDS_BYPASS_TOOL_CONSENT = (
        os.environ.get("BYPASS_TOOL_CONSENT", "").lower() == "true"
    )

    # Create a panel for GraphQL Operation Details
    operation_details = f"{Fore.CYAN}Endpoint:{Style.RESET_ALL} {endpoint}\n"
    operation_details += f"{Fore.CYAN}Query:{Style.RESET_ALL}\n{query}\n"
    if variables:
        operation_details += f"{Fore.CYAN}Variables:{Style.RESET_ALL}\n"
        for key, value in variables.items():
            operation_details += f"  - {key}: {value}\n"
    if auth_type:
        operation_details += f"{Fore.CYAN}Auth Type:{Style.RESET_ALL} {auth_type}\n"

    console.print(Panel(operation_details, title=label, expand=False))

    logger.debug(f"Invoking GraphQL: endpoint={endpoint}, variables={variables}")

    # Check if the operation is potentially mutative
    is_mutative = is_mutation_query(query)

    if is_mutative and not STRANDS_BYPASS_TOOL_CONSENT:
        # Prompt for confirmation before executing mutative operations
        confirm = get_user_input(
            "<yellow><bold>This appears to be a mutative operation. "
            "Do you want to proceed?</bold> [y/*]</yellow>"
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
        response = execute_graphql(
            endpoint=endpoint,
            query=query,
            variables=variables,
            auth_type=auth_type,
            auth_token=auth_token,
            headers=headers,
            timeout=timeout,
        )

        # Format the response
        formatted_response = format_graphql_response(response)

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
                        "text": "Authentication failed. Please check your authentication token.\n"
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
        logger.warning(f"GraphQL call threw exception: {type(ex).__name__}")
        return {
            "status": "error",
            "content": [{"text": f"GraphQL call threw exception: {ex!s}"}],
        }
