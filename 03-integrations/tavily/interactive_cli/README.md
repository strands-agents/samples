# Interactive CLI - Deep Research Agent

An intelligent terminal-based research agent powered by Strands and [Tavily](https://www.tavily.com/). This agent uses Tavily's web search, extract, and crawl APIs to gather information from reliable sources, extract key insights, and save comprehensive research reports in Markdown format.

## 🎥 Demo

<video src="https://github.com/user-attachments/assets/d873a93e-5086-4fc8-81c7-38dba12417c8" controls="controls" style="max-width: 730px;">
</video>

---

## Solution Architecture

<div align="center">
    <img src="../assets/architecture_interactive.png" alt="Interactive CLI Research Agent Architecture" width="75%" />
    <br/>
</div>

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager
- Tavily API key
- AWS credentials (for Bedrock access)

### Installation

1. **Install uv package manager:**
   See [Installing UV](https://docs.astral.sh/uv/getting-started/installation/)

2. **Navigate to the CLI directory:**
   ```bash
   cd interactive_cli
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` file and add your credentials:
   ```env
   TAVILY_API_KEY=your_tavily_api_key_here
   AWS_REGION=us-east-1
   ```

### Usage

**Run the interactive researcher:**
```bash
uv run deep_research.py
```

The agent will prompt you for a research query and then autonomously:
- 🔍 Search the web for relevant information
- 🕷️ Crawl websites for deeper insights
- 📄 Extract content from specific pages
- 📝 Generate a formatted research report
- 💾 Save results to `research_findings/` directory

---

## 💡 Example Queries

Try these research queries to get started:

```
What are the latest developments in quantum computing?
```

```
Find recent studies on climate change from 2022–2023, focusing on impact to coastal regions.
```

```
Research the current state of renewable energy adoption in Europe.
```

```
Analyze the impact of AI on software development practices in 2024.
```
