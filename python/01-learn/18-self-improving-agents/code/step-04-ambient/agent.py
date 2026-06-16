"""AIM308 - Step 4: Autonomous agent (ambient mode + optional scheduler).

Inherits memory + self-modification from step-03 and adds a background
thread that keeps working when the user is idle.
"""
import os
import sys
from datetime import datetime
from pathlib import Path

from strands import Agent
from strands_tools import shell, file_write

from tools.system_prompt import system_prompt
from ambient import AmbientMode

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
        "You are a self-improving autonomous research agent.\n"
        "Capabilities: self-extending tools, self-modifying prompts, long-term memory, "
        "and AMBIENT mode - you work in the background during user idle time."
    )
    persistent = PROMPT_FILE.read_text() if PROMPT_FILE.exists() else ""
    env_ext = os.environ.get("SYSTEM_PROMPT", "")
    parts = [base]
    if persistent:
        parts.append(f"\n## Persisted:\n{persistent}")
    if env_ext and env_ext != persistent:
        parts.append(f"\n## Env:\n{env_ext}")
    parts.append(f"\n## Runtime: {datetime.now().isoformat(timespec='seconds')}")
    return "\n".join(parts)


def make_agent():
    if not MEMORY_ID:
        print("⚠️  BEDROCK_AGENTCORE_MEMORY_ID not set. See step-03 README.")
        sys.exit(1)

    memory_config = AgentCoreMemoryConfig(
        memory_id=MEMORY_ID, session_id=SESSION_ID, actor_id=ACTOR_ID,
        retrieval_config={
            f"/users/{ACTOR_ID}/facts": RetrievalConfig(top_k=3, relevance_score=0.5),
            f"/users/{ACTOR_ID}/preferences": RetrievalConfig(top_k=3, relevance_score=0.5),
        },
    )
    memory_tools = AgentCoreMemoryToolProvider(
        memory_id=MEMORY_ID, session_id=SESSION_ID,
        actor_id=ACTOR_ID, namespace="default", region=REGION,
    ).tools

    return Agent(
        model=MODEL_ID,
        tools=[shell, file_write, system_prompt] + memory_tools,
        session_manager=AgentCoreMemorySessionManager(memory_config, REGION),
        load_tools_from_directory=True,
        system_prompt=build_system_prompt(),
    )


def main():
    print(f"🦆 Autonomous agent. Ambient mode enabled (20s idle). Type 'exit' to quit.\n")
    agent = make_agent()
    ambient = AmbientMode(agent, idle_seconds=20, max_iterations=3)
    ambient.start()

    while True:
        try:
            q = input("🦆 ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if q.lower() in ("exit", "quit", "q", ""):
            break

        ambient.interrupt()
        pending = ambient.consume_pending()
        if pending:
            q_full = (
                f"[Background exploration results from ambient mode]:\n{pending}\n\n"
                f"[User query]: {q}"
            )
        else:
            q_full = q

        agent(q_full)
        ambient.record_interaction(q)

    ambient.stop()


if __name__ == "__main__":
    main()
