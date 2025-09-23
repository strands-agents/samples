"""System prompt management tool for Strands Agents.

This module provides a tool to view and modify system prompts used by the agent.
It helps with dynamic adaptation of the agent's behavior and capabilities.

Key Features:
1. View current system prompt from any environment variable
2. Update system prompt (in-memory)
3. Add context information to system prompt
4. Reset system prompt to default
5. Support for custom variable names (SYSTEM_PROMPT, TOOL_BUILDER_SYSTEM_PROMPT, etc.)

Usage Examples:
```python
from strands import Agent
from strands_research_agent.tools import system_prompt

agent = Agent(tools=[system_prompt])

# View current system prompt (default SYSTEM_PROMPT variable)
result = agent.tool.system_prompt(action="view")

# Update system prompt
result = agent.tool.system_prompt(
    action="update",
    prompt="You are a specialized tool builder agent...",
    variable_name="TOOL_BUILDER_SYSTEM_PROMPT",
)

# Work with any custom variable name
result = agent.tool.system_prompt(
    action="view", variable_name="MY_CUSTOM_PROMPT"
)
```
"""

import os
from pathlib import Path
from strands import tool


def _get_prompt_file_path() -> Path:
    """Get the appropriate .prompt file path."""
    # Check current directory first
    current_dir_prompt = Path(".prompt")
    if current_dir_prompt.exists():
        return current_dir_prompt

    # Check /tmp/.research/ directory
    research_dir_prompt = Path("/tmp/.research/.prompt")
    if research_dir_prompt.exists():
        return research_dir_prompt

    # Default to current directory if neither exists
    return current_dir_prompt


def _write_prompt_file(prompt: str) -> None:
    """Write prompt to .prompt file."""
    prompt_file = _get_prompt_file_path()

    # Ensure parent directory exists
    prompt_file.parent.mkdir(parents=True, exist_ok=True)

    # Write prompt to file
    prompt_file.write_text(prompt, encoding="utf-8")


def _get_system_prompt(variable_name: str = "SYSTEM_PROMPT") -> str:
    """Get the current system prompt from local environment variable.

    Args:
        variable_name: Name of the environment variable to use

    Returns:
        The system prompt string
    """
    return os.environ.get(variable_name, "")


def _update_system_prompt(
    new_prompt: str, variable_name: str = "SYSTEM_PROMPT"
) -> None:
    """Update the system prompt in both environment variable and .prompt file."""
    # Update in-memory environment variable
    os.environ[variable_name] = new_prompt

    # Also write to .prompt file for persistence across sessions
    # Only write to file for the default SYSTEM_PROMPT variable to avoid conflicts
    if variable_name == "SYSTEM_PROMPT":
        _write_prompt_file(new_prompt)


@tool
def system_prompt(
    action: str,
    prompt: str | None = None,
    context: str | None = None,
    variable_name: str = "SYSTEM_PROMPT",
) -> dict[str, str | list[dict[str, str]]]:
    """Manage the agent's system prompt.

    This tool allows viewing and modifying the system prompt used by the agent.
    It can be used to adapt the agent's behavior dynamically during runtime.

    Args:
        action: The action to perform on the system prompt. One of:
            - "view": View the current system prompt
            - "update": Replace the current system prompt
            - "add_context": Add additional context to the system prompt
            - "reset": Reset to default (empty)
        prompt: New system prompt when using the "update" action
        context: Additional context to add when using the "add_context" action
        variable_name: Name of the environment variable to use
                      (default: "SYSTEM_PROMPT")

    Returns:
        A dictionary with the operation status and current system prompt

    Example:
        ```python
        # View current system prompt
        result = system_prompt(action="view")

        # Update system prompt
        result = system_prompt(
            action="update", prompt="You are a specialized agent for task X..."
        )

        # Work with custom variable name
        result = system_prompt(
            action="update",
            prompt="You are a tool builder...",
            variable_name="TOOL_BUILDER_SYSTEM_PROMPT",
        )
        ```
    """
    try:
        if action == "view":
            current_prompt = _get_system_prompt(variable_name)

            return {
                "status": "success",
                "content": [
                    {
                        "text": f"Current system prompt from {variable_name}:\n\n{current_prompt}"
                    }
                ],
            }

        elif action == "update":
            if not prompt:
                return {
                    "status": "error",
                    "content": [
                        {
                            "text": "Error: prompt parameter is required for the update action"
                        }
                    ],
                }

            # Update in-memory environment variable
            _update_system_prompt(prompt, variable_name)

            # Update message based on whether we wrote to file
            if variable_name == "SYSTEM_PROMPT":
                message = f"System prompt updated successfully (env: {variable_name}, file: .prompt)"
            else:
                message = f"System prompt updated successfully (env: {variable_name})"

            return {
                "status": "success",
                "content": [{"text": message}],
            }

        elif action == "add_context":
            if not context:
                return {
                    "status": "error",
                    "content": [
                        {
                            "text": "Error: context parameter is required for the add_context action"
                        }
                    ],
                }

            current_prompt = _get_system_prompt(variable_name)
            new_prompt = f"{current_prompt}\n\n{context}" if current_prompt else context
            _update_system_prompt(new_prompt, variable_name)

            # Update message based on whether we wrote to file
            if variable_name == "SYSTEM_PROMPT":
                message = f"Context added to system prompt successfully (env: {variable_name}, file: .prompt)"
            else:
                message = f"Context added to system prompt successfully (env: {variable_name})"

            return {
                "status": "success",
                "content": [{"text": message}],
            }

        elif action == "reset":
            # Reset environment variable
            os.environ.pop(variable_name, None)

            # Also clear .prompt file for SYSTEM_PROMPT variable
            if variable_name == "SYSTEM_PROMPT":
                prompt_file = _get_prompt_file_path()
                if prompt_file.exists():
                    prompt_file.unlink()  # Delete the file
                message = f"System prompt reset to default (env: {variable_name}, file: .prompt cleared)"
            else:
                message = f"System prompt reset to default (env: {variable_name})"

            return {
                "status": "success",
                "content": [{"text": message}],
            }

        else:
            return {
                "status": "error",
                "content": [
                    {
                        "text": f"Error: Unknown action '{action}'. Valid actions are view, update, add_context, reset"
                    }
                ],
            }

    except Exception as e:
        return {"status": "error", "content": [{"text": f"Error: {e!s}"}]}
