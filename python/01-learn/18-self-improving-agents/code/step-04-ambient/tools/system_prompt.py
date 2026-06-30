"""The system_prompt tool. Gives the agent control over its own identity."""
import os
from pathlib import Path
from strands import tool

PROMPT_FILE = Path(".prompt")


@tool
def system_prompt(action: str, prompt: str | None = None) -> dict:
    """Manage the agent's own system prompt at runtime.

    Args:
        action: One of "view", "update", "add_context", "reset".
        prompt: The new prompt text (required for update / add_context).

    Returns:
        Dict with status and content.
    """
    if action == "view":
        current = os.environ.get("SYSTEM_PROMPT", "") or (
            PROMPT_FILE.read_text() if PROMPT_FILE.exists() else ""
        )
        return {"status": "success", "content": [{"text": current or "(empty)"}]}

    if action == "update":
        if not prompt:
            return {"status": "error", "content": [{"text": "prompt required"}]}
        os.environ["SYSTEM_PROMPT"] = prompt
        PROMPT_FILE.write_text(prompt)
        return {
            "status": "success",
            "content": [{"text": f"Prompt updated & persisted ({len(prompt)} chars)."}],
        }

    if action == "add_context":
        if not prompt:
            return {"status": "error", "content": [{"text": "prompt required"}]}
        existing = os.environ.get("SYSTEM_PROMPT", "")
        merged = f"{existing}\n\n{prompt}" if existing else prompt
        os.environ["SYSTEM_PROMPT"] = merged
        PROMPT_FILE.write_text(merged)
        return {"status": "success", "content": [{"text": "Context appended."}]}

    if action == "reset":
        os.environ.pop("SYSTEM_PROMPT", None)
        if PROMPT_FILE.exists():
            PROMPT_FILE.unlink()
        return {"status": "success", "content": [{"text": "Prompt reset to default."}]}

    return {"status": "error", "content": [{"text": f"Unknown action: {action}"}]}
