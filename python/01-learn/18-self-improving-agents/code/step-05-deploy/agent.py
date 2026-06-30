"""AIM308 - Step 5: Deploy to Amazon Bedrock AgentCore Runtime.

Wraps the fully-featured research agent as an AgentCore app. Run locally with
`python agent.py` (falls through to app.run()), or deploy to AWS with the
new @aws/agentcore CLI (https://github.com/aws/agentcore-cli):

    ./deploy.sh

which runs:

    agentcore create --name Aim308Deploy --no-agent --defaults
    agentcore add agent --name aim308_research_agent --type byo \
        --language Python --framework Strands --model-provider Bedrock \
        --code-location <this dir> --entrypoint agent.py --protocol HTTP
    agentcore deploy -y

AWS_REGION and BEDROCK_AGENTCORE_MEMORY_ID are injected into
Aim308Deploy/agentcore/.env.local so the deployed runtime sees them.
"""
import os
import socket
import threading
from datetime import datetime
from pathlib import Path

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from strands import Agent
from strands_tools import shell, file_write

from tools.system_prompt import system_prompt

from bedrock_agentcore.memory.integrations.strands.config import (
    AgentCoreMemoryConfig,
    RetrievalConfig,
)
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager,
)
from strands_tools.agent_core_memory import AgentCoreMemoryToolProvider

MODEL_ID = os.environ.get("BEDROCK_AGENTCORE_MODEL_ID")
PROMPT_FILE = Path(".prompt")

MEMORY_ID = os.environ.get("BEDROCK_AGENTCORE_MEMORY_ID")
REGION = os.environ.get("AWS_REGION", "us-east-1")

app = BedrockAgentCoreApp()


def build_system_prompt(q: str = "") -> str:
    base = (
        "You are a production-deployed, self-improving research agent running "
        "on Amazon Bedrock AgentCore Runtime.\n\n"
        "Capabilities:\n"
        "- Self-extending tools (`load_tools_from_directory=True`)\n"
        "- Self-modifying system prompt (the `system_prompt` tool)\n"
        "- Long-term memory (AgentCore Memory, per-actor namespaces)\n"
        "- Shell & file access\n"
    )
    persistent = PROMPT_FILE.read_text() if PROMPT_FILE.exists() else ""
    env_ext = os.environ.get("SYSTEM_PROMPT", "")
    runtime = (
        f"\n## Runtime: {datetime.now().isoformat(timespec='seconds')} "
        f"(host={socket.gethostname()}) deployed=AgentCore\n"
    )
    parts = [base]
    if persistent:
        parts.append(f"\n## Persisted:\n{persistent}")
    if env_ext and env_ext != persistent:
        parts.append(f"\n## Env:\n{env_ext}")
    parts.append(runtime)
    if q:
        parts.append(f"\n## User query (routed from AgentCore):\n{q}\n")
    return "\n".join(parts)


def make_agent(session_id: str, actor_id: str):
    memory_config = AgentCoreMemoryConfig(
        memory_id=MEMORY_ID, session_id=session_id, actor_id=actor_id,
        retrieval_config={
            f"/users/{actor_id}/facts": RetrievalConfig(top_k=3, relevance_score=0.5),
            f"/users/{actor_id}/preferences": RetrievalConfig(top_k=3, relevance_score=0.5),
        },
    ) if MEMORY_ID else None

    memory_tools = (
        AgentCoreMemoryToolProvider(
            memory_id=MEMORY_ID, session_id=session_id,
            actor_id=actor_id, namespace="default", region=REGION,
        ).tools
        if MEMORY_ID else []
    )

    return Agent(
        model=MODEL_ID,
        tools=[shell, file_write, system_prompt] + memory_tools,
        session_manager=(
            AgentCoreMemorySessionManager(memory_config, REGION)
            if memory_config else None
        ),
        load_tools_from_directory=True,
        system_prompt=build_system_prompt(),
    )


@app.entrypoint
def invoke(payload, context):
    """AgentCore HTTP entrypoint — returns the response, then continues working in background."""
    session_id = getattr(context, "session_id", "default")
    actor_id = "user"
    headers = getattr(context, "headers", {}) or {}
    actor_id = headers.get(
        "X-Amzn-Bedrock-AgentCore-Runtime-Custom-Actor-Id", actor_id
    )

    q = payload.get("prompt", "")
    agent = make_agent(session_id=session_id, actor_id=actor_id)
    result = agent(q)

    # Background: continue exploring the topic (ambient/self-improving behavior)
    def _background_explore():
        try:
            follow_up = (
                f"You just answered: '{q}'. "
                f"Now proactively explore edge cases, improvements, or related topics. "
                f"Save any useful findings to your system prompt for future use."
            )
            bg_agent = make_agent(session_id=session_id, actor_id=actor_id)
            bg_agent(follow_up)
        except Exception as e:
            print(f"[background explore] {e}")

    threading.Thread(target=_background_explore, daemon=True).start()

    return {"response": str(result)}


if __name__ == "__main__":
    # Local dev server - emulates AgentCore locally.
    app.run()
