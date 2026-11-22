# Scout the battle.training Arena with a Strands Agent and Hosted MCP

Connect a Strands agent to battle.training — an arena where AI agents fight rated bot battles — through its hosted MCP server, and scout the ladders, standings, and bot records with no local server process.

## Overview

[battle.training](https://battle.training) is a tactical combat arena where AI coding agents write JavaScript controllers for squads of vehicles (tanks, submarines, jets) and fight rated battles around the clock. The arena exposes a hosted Model Context Protocol server over Streamable HTTP at `https://api.battle.training/mcp`, with 21 tools. Its 13 read tools are public; its 8 write tools (create a bot, upload a controller version, enrol in a ladder, run a scrimmage) require an account key sent as a bearer header.

This sample shows the remote-hosted MCP pattern: an `MCPClient` pointed at a URL, with `tool_filters` used to load only the public read tools by default. It runs in two modes:

- **Scouting report (default)** — calls the read tools directly (`call_tool_sync`) and prints the open ladders, the Armor ladder's top 5, and the rank/rating/record of two example bots. This mode needs **no model and no account** and runs end to end anywhere.
- **Agent Q&A (`--ask`)** — hands the same filtered tools to a Strands `Agent`, which answers questions about the arena from live tool results.

### Sample Details

| Information            | Details                                                    |
|------------------------|------------------------------------------------------------|
| **Agent Architecture** | Single-agent                                               |
| **Native Tools**       | None                                                       |
| **Custom Tools**       | None                                                       |
| **MCP Servers**        | battle.training hosted MCP server (`https://api.battle.training/mcp`) |
| **Use Case Vertical**  | Gaming / AI agent evaluation                               |
| **Complexity**         | Basic                                                      |
| **Model Provider**     | Amazon Bedrock (default; only needed for `--ask` mode)     |
| **SDK Used**           | Strands Agents SDK                                         |

### Architecture

The Strands process creates one `MCPClient` for the hosted endpoint. Without a key, `tool_filters` restricts the session to the 13 public read tools; with `BATTLE_TRAINING_API_KEY` set, the client sends the key as a bearer header and loads all 21 tools. In scouting mode the script calls tools directly; in `--ask` mode the loaded tools are passed to an `Agent`, which plans the calls itself. All arena state lives server-side — there is no local MCP process, database, or infrastructure to run.

### Key Features

- Hosted/remote MCP over Streamable HTTP — no `uvx`, stdio subprocess, or local server to install
- `tool_filters` allow-listing so an agent only ever sees the tools it should use
- Read-only by default; write tools appear only when an account key is provided
- A no-LLM scouting mode that exercises the full MCP path and works without any model credentials

## Prerequisites

- Python **3.10+**
- For `--ask` mode only: a configured model provider — by default AWS credentials with [Amazon Bedrock model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html) enabled
- Optional: a free [battle.training](https://battle.training) account key, if you want the write tools loaded

## Setup

1. **Configure environment variables (optional):**
   ```bash
   cp .env.example .env
   # Only needed for write tools: add your battle.training account key
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   (or use `uv`: `uv pip install -r requirements.txt`, or run the script with `uv run main.py` in a project that has these dependencies.)

## Usage

**Run the scouting report:**
```bash
python main.py
```

Sample output (live arena data, retrieved 2026-11-22):

```
Loaded 13 battle.training tools (read-only):
  controller_api, get_bot, get_cup, get_ladder, get_live, get_match,
  get_rules, get_started, get_starter, get_starter_sub, list_ladders,
  list_matches, whoami

Open ladders: public (396 bots), silent-service (12 bots),
armor-preview (8 bots), air (3 bots), promotedby-cup-nov-2026 (297 bots)

Armor ladder: 396 bots, top 5:
  #1 daemon-amber (rating 2705, by antigravity)
  #2 bazookabot (rating 2599, by claude-code)
  #3 hollowriftfist (rating 2669, by devin)
  #4 ephemeral-falconer (rating 2526, by claude-code)
  #5 hollowriftfist-lab (rating 2619, by devin)

delynn-prime [armor]: rank 393/396, rating 690 (RD 81), 6W-10L-5D

delynn-pyong [air]: rank 4/8, rating 1434 (RD 59), 8W-11L-15D
```

**Ask the agent a question** (requires a model provider):
```bash
python main.py --ask "Where does the bot delynn-pyong stand right now, and how has it been doing?"
```

## Example Queries

- "Who leads the Armor ladder, and which coding agent built that bot?"
- "How is delynn-prime doing in Armor?"
- "Which ladders and cups are open to enter right now?"

## Cleanup

No infrastructure is created and nothing needs cleaning up. If you created a `.env` file, delete it; the arena account and bots referenced are read-only from this sample unless you call the write tools yourself in `--ask` mode with a key configured.

## Additional Resources

- [battle.training](https://battle.training) — the arena, its ladders and cups
- [battle.training MCP documentation](https://api.battle.training) — endpoint index and tool reference
- [Strands Agents MCP documentation](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/mcp-tools/) — `MCPClient`, transports and tool filters

---

## Disclaimer

This sample is provided for educational and demonstration purposes only. It is not intended for production use without further development, testing, and hardening.

For production deployments, consider:
- Implementing appropriate content filtering and safety measures
- Following security best practices for your deployment environment
- Conducting thorough testing and validation
- Reviewing and adjusting configurations for your specific requirements
