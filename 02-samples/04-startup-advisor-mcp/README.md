# Startup Advisor using Perplexity MCP server

Have a new startup in mind, but haven't quite hired your marketing staff? Use this Startup Advisrt agent to do your market research, come up with campaign ideas, and write effective campaign copy.

![architecture](./architecture.png)

|Feature             |Description                                        |
|--------------------|---------------------------------------------------|
|Agent Structure     | Multi-agent architecture                          |
|Native Tools        |swarm, file_write, editor                          |
|Custom Agents       |market_research_team, writer_team                  |
|MCP Servers         |[Perplexity search](https://github.com/jsonallen/perplexity-mcp)|
|Model Provider      |Amazon Bedrock                                     |

## Key Features

- Shows Sequential mult-agent architecture using Strands Agent
- Agentic search using Perplexity MCP server.
- Utilizes `Swarm` tool, allowing collaboration bettween swarm of agents to do market research.

## Prerequisites

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).

2. Create .env file with [.env.example](./.env.example). Follow guidance [here](https://docs.perplexity.ai/guides/getting-started) to get started with perplexity AI.

3. Run `uv run main.py`
