# 🌐 Web Researcher Agent

An intelligent terminal-based research assistant powered by Strands and [Tavily](https://www.tavily.com/). This agent uses Tavily's web search API to gather information from reliable sources, extract key insights, and save comprehensive research reports in Markdown format.

![architecture](./architecture.png)

|Feature             |Description                                        |
|--------------------|---------------------------------------------------|
|Agent Structure     |Single-agent architecture                          |
|Custom Agents       |tavily_search, write_md_file                       |
|Model Provider      |Amazon Bedrock                                     |

## ✨ Features

- Interactive terminal-based interface
- Tavily-powered web search with caching
- Automatically saves research findings as `.md` files
- Well-structured output with citations
- Supports .env file for secure API key loading

## Getting Started

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).

2. Set up AWS credentials in `.env` using [.env.example](./.env.example).

3. Run the SCRUM Master Assistant using `uv run main.py`
