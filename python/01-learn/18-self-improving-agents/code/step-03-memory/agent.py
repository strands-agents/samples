"""AIM308 - Step 3: Self-learning agent (AgentCore Memory).

Adds long-term memory via Amazon Bedrock AgentCore Memory. The agent
automatically retrieves relevant past conversations before each answer
and stores new interactions for future.
"""
import os
import sys
from datetime import datetime
from pathlib import Path

from strands import Agent
from strands_tools import shell, file_write

from tools.system_prompt import system_prompt

# AgentCore Memory imports
from bedrock_agentcore.memory.integrations.strands.config import (
    AgentCoreMemoryConfig,
    RetrievalConfig,
)
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager,
)
from strands_tools.agent_core_memory import AgentCoreMemoryToolProvider

MODEL_ID = "global.anthropic.claude-opus-4-8"
PROMPT_FILE = Path(".prompt")

MEMORY_ID = os.environ.get("BEDROCK_AGENTCORE_MEMORY_ID")
REGION = os.environ.get("AWS_REGION", "us-east-1")
ACTOR_ID = os.environ.get("USER", "attendee")
SESSION_ID = f"aim308-{ACTOR_ID}"


def build_system_prompt() -> str:
    base = (
        "You are a self-improving research agent with long-term memory.\n"
        "Before answering, consult your memory. After answering, save useful "
        "facts and user preferences.\n"
        "You can also modify your own system prompt via the system_prompt tool."
    )
    persistent = PROMPT_FILE.read_text() if PROMPT_FILE.exists() else ""
    env_ext = os.environ.get("SYSTEM_PROMPT", "")
    runtime = (
        f"\n## Runtime: {datetime.now().isoformat(timespec='seconds')} | "
        f"actor={ACTOR_ID} | session={SESSION_ID}\n"
    )
    parts = [base]
    if persistent:
        parts.append(f"\n## Persisted:\n{persistent}")
    if env_ext and env_ext != persistent:
        parts.append(f"\n## Env:\n{env_ext}")
    parts.append(runtime)
    return "\n".join(parts)


def make_agent():
    if not MEMORY_ID:
        print(
            "⚠️  BEDROCK_AGENTCORE_MEMORY_ID not set. "
            "Create one first (see README) and export it."
        )
        sys.exit(1)

    memory_config = AgentCoreMemoryConfig(
        memory_id=MEMORY_ID,
        session_id=SESSION_ID,
        actor_id=ACTOR_ID,
        retrieval_config={
            f"/users/{ACTOR_ID}/facts": RetrievalConfig(top_k=3, relevance_score=0.5),
            f"/users/{ACTOR_ID}/preferences": RetrievalConfig(top_k=3, relevance_score=0.5),
        },
    )

    memory_tools = AgentCoreMemoryToolProvider(
        memory_id=MEMORY_ID,
        session_id=SESSION_ID,
        actor_id=ACTOR_ID,
        namespace="default",
        region=REGION,
    ).tools

    return Agent(
        model=MODEL_ID,
        tools=[shell, file_write, system_prompt] + memory_tools,
        session_manager=AgentCoreMemorySessionManager(memory_config, REGION),
        load_tools_from_directory=True,
        system_prompt=build_system_prompt(),
    )


def main():
    print(f"🦆 Self-learning agent (memory={MEMORY_ID}, actor={ACTOR_ID}).\n")
    agent = make_agent()
    while True:
        try:
            q = input("🦆 ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if q.lower() in ("exit", "quit", "q", ""):
            break
        agent(q)


if __name__ == "__main__":
    main()
