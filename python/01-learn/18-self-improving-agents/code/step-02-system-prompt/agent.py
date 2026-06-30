"""AIM308 - Step 2: Self-modifying agent.

Adds a `system_prompt` tool the agent can use to rewrite its own instructions.
Prompt is dynamically reconstructed every turn from multiple sources, so
modifications stick - even across restarts.
"""
import os
import socket
import sys
from datetime import datetime
from pathlib import Path

from strands import Agent
from strands_tools import shell, file_write

from tools.system_prompt import system_prompt

MODEL_ID = "global.anthropic.claude-opus-4-8"
PROMPT_FILE = Path(".prompt")


def build_system_prompt() -> str:
    """Reconstruct the system prompt from multiple sources every turn."""
    base = (
        "You are a self-improving research agent.\n"
        "You can MODIFY YOUR OWN SYSTEM PROMPT using the system_prompt tool.\n"
        "Actions: view, update, add_context, reset.\n"
        "When a user asks you to change your behavior 'permanently' or "
        "'from now on', call system_prompt(action='update', prompt=...)."
    )
    persistent = PROMPT_FILE.read_text() if PROMPT_FILE.exists() else ""
    env_extension = os.environ.get("SYSTEM_PROMPT", "")
    runtime = (
        f"\n## Runtime:\n"
        f"- Time: {datetime.now().isoformat(timespec='seconds')}\n"
        f"- Host: {socket.gethostname()}\n"
        f"- User: {os.environ.get('USER', 'unknown')}\n"
        f"- CWD: {Path.cwd()}\n"
    )
    parts = [base]
    if persistent and persistent != env_extension:
        parts.append(f"\n## Persisted (.prompt):\n{persistent}")
    if env_extension and env_extension != persistent:
        parts.append(f"\n## Env SYSTEM_PROMPT:\n{env_extension}")
    parts.append(runtime)
    return "\n".join(parts)


def main():
    print("🦆 Self-modifying agent. Type 'exit' to quit.\n")
    while True:
        try:
            q = input("🦆 ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if q.lower() in ("exit", "quit", "q", ""):
            break

        # Rebuild agent each turn so system_prompt updates take effect immediately.
        agent = Agent(
            model=MODEL_ID,
            tools=[shell, file_write, system_prompt],
            load_tools_from_directory=True,
            system_prompt=build_system_prompt(),
        )
        agent(q)


if __name__ == "__main__":
    main()
