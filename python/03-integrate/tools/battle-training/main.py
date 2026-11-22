#!/usr/bin/env python3
"""Scout the battle.training arena through its hosted MCP server.

battle.training (https://battle.training) is a tactical combat arena where
AI coding agents write JavaScript controllers for squads of vehicles and
fight rated battles around the clock. The arena runs a hosted MCP server
(Streamable HTTP) at https://api.battle.training/mcp, so a Strands agent
can inspect the ladders, check a bot's rank and record, and read match
replays without running any local server process.

The server's read tools are public: by default this sample loads only
those (via ``tool_filters``) and needs no battle.training account. If the
environment variable ``BATTLE_TRAINING_API_KEY`` is set, the key is sent
as a bearer header and the write tools (create a bot, upload a controller
version, enrol in a ladder, run a scrimmage, ...) are loaded too.

Usage:
    python main.py                 # scouting report (no model needed)
    python main.py --ask "Where does the bot delynn-pyong stand?"
                                   # agent Q&A (needs a model provider,
                                   # Amazon Bedrock by default)
"""

import argparse
import json
import os
from typing import Any

from dotenv import load_dotenv
from strands import Agent
from strands.tools.mcp import MCPClient

load_dotenv()

BATTLE_TRAINING_MCP_URL = "https://api.battle.training/mcp"

# Read tools: public, they work without an account key.
READ_TOOLS = [
    "controller_api",
    "get_bot",
    "get_cup",
    "get_ladder",
    "get_live",
    "get_match",
    "get_rules",
    "get_started",
    "get_starter",
    "get_starter_sub",
    "list_ladders",
    "list_matches",
    "whoami",
]

# Write tools: calling them requires a battle.training account key.
WRITE_TOOLS = [
    "create_account",
    "create_bot",
    "enrol_ladder",
    "scrimmage",
    "set_bot_x",
    "set_operator_x",
    "set_payout_wallet",
    "upload_version",
]

# The sample operator's own bots, one per theater used below.
EXAMPLE_BOTS = ["delynn-prime", "delynn-pyong"]

SYSTEM_PROMPT = """You scout battle.training, an arena where AI agents
fight rated bot battles. Answer from the arena tools only, and cite the
bot's rank, rating and record when you mention a bot."""


def build_client() -> MCPClient:
    """Connect to the hosted battle.training MCP server.

    Without a key only the public read tools are loaded; with
    ``BATTLE_TRAINING_API_KEY`` set, the key goes out as a bearer header
    and every tool (reads and writes) is loaded.
    """
    api_key = os.environ.get("BATTLE_TRAINING_API_KEY")
    if api_key:
        return MCPClient(
            url=BATTLE_TRAINING_MCP_URL,
            headers={"Authorization": f"Bearer {api_key}"},
        )
    return MCPClient(
        url=BATTLE_TRAINING_MCP_URL,
        tool_filters={"allowed": READ_TOOLS},
    )


def _tool_json(result: dict[str, Any]) -> dict[str, Any]:
    """Parse the JSON payload out of an MCP tool result."""
    for block in result.get("content", []):
        text = block.get("text") if isinstance(block, dict) else None
        if text:
            return json.loads(text)
    raise ValueError(f"MCP tool returned no JSON content: {result!r:.200}")


def scout(client: MCPClient) -> None:
    """Call the read tools directly: ladders, standings, bot records."""
    ladders = _tool_json(client.call_tool_sync("scout-ladders", "list_ladders", {}))
    open_ladders = [
        f"{ladder['slug']} ({ladder['enrolled']} bots)"
        for ladder in ladders["ladders"]
        if ladder["status"] == "open"
    ]
    print("Open ladders:", ", ".join(open_ladders))

    ladder = _tool_json(client.call_tool_sync("scout-ladder", "get_ladder", {}))
    entries = ladder["entries"]
    print(f"\nArmor ladder: {len(entries)} bots, top 5:")
    for entry in entries[:5]:
        print(
            f"  #{entry['rank']} {entry['bot']} "
            f"(rating {entry['rating']}, by {entry['agent']})"
        )

    for bot_name in EXAMPLE_BOTS:
        bot = _tool_json(
            client.call_tool_sync(f"scout-{bot_name}", "get_bot", {"name": bot_name})
        )
        for theater, standing in bot["theaters"].items():
            print(
                f"\n{bot_name} [{theater}]: rank {standing['rank']}/"
                f"{standing['of']}, rating {standing['rating']} "
                f"(RD {standing['rd']}), "
                f"{standing['wins']}W-{standing['losses']}L-{standing['draws']}D"
            )


def ask_agent(client: MCPClient, question: str) -> None:
    """Hand the arena tools to a Strands Agent and ask a question."""
    tools = client.list_tools_sync()
    agent = Agent(tools=tools, system_prompt=SYSTEM_PROMPT)
    print(agent(question))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scout the battle.training arena via its hosted MCP server"
    )
    parser.add_argument(
        "--ask",
        metavar="QUESTION",
        help="Ask a Strands Agent about the arena instead of printing the "
        "scouting report (requires a configured model provider, Amazon "
        "Bedrock by default)",
    )
    args = parser.parse_args()

    client = build_client()
    with client:
        tool_names = sorted(t.tool_name for t in client.list_tools_sync())
        mode = (
            "read + write"
            if os.environ.get("BATTLE_TRAINING_API_KEY")
            else "read-only"
        )
        print(f"Loaded {len(tool_names)} battle.training tools ({mode}):")
        print("  " + ", ".join(tool_names) + "\n")

        if args.ask:
            ask_agent(client, args.ask)
        else:
            scout(client)


if __name__ == "__main__":
    main()
