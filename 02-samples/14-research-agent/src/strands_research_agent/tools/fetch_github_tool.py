"""GitHub Tool Fetcher for Strands Agent.

This tool fetches Python tool files from GitHub repositories and loads them
as available tools in the current Strands agent. It combines HTTP fetching
with the load_tool functionality to enable dynamic tool loading from remote
GitHub repositories.

Usage with Strands Agents:
python
from strands import Agent
from tools.fetch_github_tool import fetch_github_tool

agent = Agent(tools=[fetch_github_tool])

# Fetch and load a tool from GitHub
agent.tool.fetch_github_tool(
    github_url="https://github.com/owner/repo/blob/main/tools/my_tool.py",
    tool_name="my_tool"
)

# Now you can use the fetched tool
agent.tool.my_tool(param1="value")


Supported GitHub URL formats:
- https://github.com/owner/repo/blob/branch/path/to/file.py
- https://github.com/owner/repo/tree/branch/path/to/file.py
- https://raw.githubusercontent.com/owner/repo/branch/path/to/file.py
"""

import os
import re
from pathlib import Path
from typing import Any

import requests
from strands import tool


def parse_github_url(github_url: str) -> dict[str, str]:
    """Parse GitHub URL to extract repository information.

    Args:
        github_url: GitHub URL to the file

    Returns:
        Dictionary with owner, repo, branch, and file_path

    Raises:
        ValueError: If URL format is not supported
    """
    # Handle raw.githubusercontent.com URLs
    raw_pattern = r"https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)"
    raw_match = re.match(raw_pattern, github_url)

    if raw_match:
        owner, repo, branch, file_path = raw_match.groups()
        return {"owner": owner, "repo": repo, "branch": branch, "file_path": file_path}

    # Handle github.com/owner/repo/blob/branch/path URLs
    blob_pattern = r"https://github\.com/([^/]+)/([^/]+)/(?:blob|tree)/([^/]+)/(.+)"
    blob_match = re.match(blob_pattern, github_url)

    if blob_match:
        owner, repo, branch, file_path = blob_match.groups()
        return {"owner": owner, "repo": repo, "branch": branch, "file_path": file_path}

    raise ValueError(f"Unsupported GitHub URL format: {github_url}")


def build_raw_url(owner: str, repo: str, branch: str, file_path: str) -> str:
    """Build GitHub raw content URL.

    Args:
        owner: Repository owner
        repo: Repository name
        branch: Branch name
        file_path: Path to file in repository

    Returns:
        Raw GitHub URL for the file
    """
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"


@tool
def fetch_github_tool(
    github_url: str,
    tool_name: str | None = None,
    local_dir: str = "./github_tools",
    agent: Any = None,
) -> dict[str, Any]:
    """Fetch a Python tool file from GitHub and load it as a Strands tool.

    This tool downloads Python files from GitHub repositories, saves them locally,
    and registers them as available tools in the current Strands agent. It supports
    various GitHub URL formats and automatically handles the conversion to raw content URLs.

    Args:
        github_url: GitHub URL to the Python tool file. Supports formats like:
            - https://github.com/owner/repo/blob/main/tools/my_tool.py
            - https://github.com/owner/repo/tree/main/tools/my_tool.py
            - https://raw.githubusercontent.com/owner/repo/main/tools/my_tool.py
        tool_name: Name to register the tool under. If not provided, will extract
            from the filename (e.g., "my_tool.py" becomes "my_tool")
        local_dir: Local directory to save the fetched tool file. Defaults to "./github_tools"
        agent: Agent instance (automatically provided by Strands)

    Returns:
        Dict containing status and response content:
        {
            "status": "success|error",
            "content": [{"text": "Response message"}]
        }

    Examples:
        # Fetch a tool from GitHub and load it
        agent.tool.fetch_github_tool(
            github_url="https://github.com/cagataycali/my-tools/blob/main/weather_tool.py",
            tool_name="weather"
        )

        # Tool name can be auto-detected from filename
        agent.tool.fetch_github_tool(
            github_url="https://github.com/cagataycali/my-tools/blob/main/calculator.py"
        )
    """
    try:
        # Parse the GitHub URL
        try:
            url_info = parse_github_url(github_url)
        except ValueError as e:
            return {"status": "error", "content": [{"text": f"❌ {e!s}"}]}

        # Extract tool name from filename if not provided
        if not tool_name:
            filename = os.path.basename(url_info["file_path"])
            tool_name = os.path.splitext(filename)[0]

        # Check if it's a Python file first (before making HTTP request)
        if not url_info["file_path"].endswith(".py"):
            return {
                "status": "error",
                "content": [
                    {
                        "text": f"❌ File must be a Python file (.py), got: {url_info['file_path']}"
                    }
                ],
            }

        # Build raw GitHub URL
        raw_url = build_raw_url(
            url_info["owner"],
            url_info["repo"],
            url_info["branch"],
            url_info["file_path"],
        )

        # Create local directory if it doesn't exist
        local_path = Path(local_dir)
        local_path.mkdir(parents=True, exist_ok=True)

        # Download the file
        response = requests.get(raw_url, timeout=30)
        response.raise_for_status()
        # Save the file locally
        local_file_path = local_path / f"{tool_name}.py"
        with open(local_file_path, "w", encoding="utf-8") as f:
            f.write(response.text)

        # Load the tool using load_tool functionality
        if agent and hasattr(agent, "tool_registry"):
            agent.tool_registry.load_tool_from_filepath(
                tool_name=tool_name, tool_path=str(local_file_path)
            )

            success_message = f"""✅ Successfully fetched and loaded GitHub tool!

📂 **Source:** {github_url}
🏷️  **Tool Name:** {tool_name}
💾 **Local Path:** {local_file_path}
🔧 **Status:** Ready to use

You can now use the tool with: agent.tool.{tool_name}(...)"""

            return {"status": "success", "content": [{"text": success_message}]}
        else:
            return {
                "status": "error",
                "content": [
                    {"text": "❌ Agent instance not available for tool registration"}
                ],
            }

    except requests.RequestException as e:
        return {
            "status": "error",
            "content": [{"text": f"❌ Failed to download file from GitHub: {e!s}"}],
        }
    except Exception as e:
        return {"status": "error", "content": [{"text": f"❌ Unexpected error: {e!s}"}]}
