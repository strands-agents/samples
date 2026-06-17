"""
Pokemon Team Advisor: Context Management + Shell + Evals Demo

An agent that picks the best Pokémon for competitive team building.
Demonstrates:
- context_manager="auto" (offloads large API responses, summarizes old turns)
- Strands Shell via MCP (sandboxed jq/grep for querying offloaded content)
- Large tool responses handled transparently by the context offloader

Data: PokeAPI/api-data JSON files (run ./setup.sh first)
"""

import os
from pathlib import Path
from mcp import stdio_client, StdioServerParameters
from strands import Agent, tool
from strands.tools.mcp import MCPClient
from strands.vended_plugins.context_offloader import ContextOffloader, FileStorage

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "pokedata"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
CONFIG_PATH = BASE_DIR / "sandbox.toml"
ARTIFACTS_DIR.mkdir(exist_ok=True)


@tool
def get_pokemon(name_or_id: str) -> str:
    """Look up a Pokémon by name or Pokédex ID. Returns full JSON with stats, types, abilities, and move list."""
    path = DATA_DIR / "pokemon" / str(name_or_id) / "index.json"
    with open(path) as f:
        return f.read()


@tool
def get_move(move_id: str) -> str:
    """Look up a move by ID. Returns full JSON including power, type, accuracy, and which Pokémon can learn it."""
    path = DATA_DIR / "move" / str(move_id) / "index.json"
    with open(path) as f:
        return f.read()


shell = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="uvx", args=["strands-shell", "--config", str(CONFIG_PATH), "--mcp"])
))

agent = Agent(
    tools=[get_pokemon, get_move, shell],
    context_manager="auto",
    plugins=[
        ContextOffloader(
            storage=FileStorage(str(ARTIFACTS_DIR)),
            include_retrieval_tool=False,
        ),
    ],
    system_prompt="Offloaded content is accessible in the shell at /artifacts/",
)

TASK = (
    "I'm building a competitive team and need a physical attacker with good "
    "coverage. Which Pokémon that can learn both Earthquake and Ice Beam has "
    "the highest base Attack stat?"
)

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(line_buffering=True)
    print(f"Task: {TASK}\n{'=' * 60}\n")
    agent(TASK)
    print(f"\n{'=' * 60}")
    offloaded = [f for f in os.listdir(ARTIFACTS_DIR) if not f.startswith('.')]
    print(f"Offloaded artifacts ({len(offloaded)})")
