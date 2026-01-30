# Deep Research Assistant with Exa Search API

A conversational AI agent that demonstrates the full power of Exa's search and content extraction capabilities through a practical research workflow using Strands Agents.

## Overview

[Exa](https://exa.ai/) is a search API specifically designed for AI applications. Unlike traditional search engines, Exa provides semantic search capabilities, content extraction, and structured output that AI agents can directly consume. This integration demonstrates how to build a Deep Research Assistant using Strands Agents and Exa's powerful search tools.

## Exa Capabilities Demonstrated

| Feature | Description |
|---------|-------------|
| Auto Mode | Intelligent hybrid of neural + keyword search for optimal results |
| Category Filtering | Specialized searches for news, PDF documents, and GitHub repositories |
| Date Filtering | Time-bound searches for recent content (e.g., last 30 days) |
| AI Summaries | Automatic key insights extraction from search results |
| Structured Output | JSON schema for structured summary extraction |
| Subpage Crawling | Discover related pages (citations, methodology, references) |
| Subpage Targeting | Keywords to find specific subpages (references, bibliography) |
| Live Crawling | Fresh content retrieval, bypassing cache |
| Content Extraction | Full text retrieval with character limit control |

## Architecture

The Deep Research Assistant implements a comprehensive 6-step research workflow:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Deep Research Assistant                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────┐     ┌──────────────────┐     ┌─────────────────┐   │
│  │  User     │────▶│  Strands Agent   │────▶│   Exa Tools     │   │
│  │  Query    │     │  (Claude/Bedrock)│     │                 │   │
│  └───────────┘     └──────────────────┘     │  • exa_search   │   │
│                             │               │  • exa_get_     │   │
│                             │               │    contents     │   │
│                             ▼               └─────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              6-Step Research Workflow                        │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ 1. Overview Search  │ Auto mode + subpages + AI summaries   │  │
│  │ 2. News Search      │ Category: news + date filtering       │  │
│  │ 3. Academic Papers  │ Category: pdf + structured output     │  │
│  │ 4. GitHub Projects  │ Category: github                      │  │
│  │ 5. Deep Dive        │ exa_get_contents + live crawling      │  │
│  │ 6. Synthesis        │ Comprehensive research brief          │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Research Output Structure

The agent produces a comprehensive research brief including:

- **Executive Summary** - 2-3 sentence overview
- **Topic Overview** - Key concepts and background
- **Recent Developments** - Latest news and announcements
- **Key Research & Papers** - Academic findings
- **Tools & Implementations** - GitHub projects and libraries
- **Deep Dive Insights** - Detailed content extraction
- **Sources** - All URLs organized by category

## Prerequisites

1. **Python 3.11+** - Required Python version
2. **[uv](https://docs.astral.sh/uv/getting-started/installation/)** - Fast Python package manager
3. **AWS Credentials** - Configure AWS CLI for Bedrock access:
   ```bash
   aws configure
   ```
4. **Exa API Key** - Get one at [dashboard.exa.ai/api-keys](https://dashboard.exa.ai/api-keys)

## Getting Started

1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your Exa API key:
   ```bash
   EXA_API_KEY=your-exa-api-key-here
   ```

3. Run the Deep Research Assistant:

   **Using uv (recommended)**
   ```bash
   uv run deep_research_assistant.py
   
   # Or with a specific research query
   uv run deep_research_assistant.py "What are the latest advances in quantum computing?"
   ```

   **Using pip**
   ```bash
   pip install -r requirements.txt
   python deep_research_assistant.py
   ```

## Usage Options

### Interactive Mode

Run without arguments to enter interactive mode:

```bash
uv run deep_research_assistant.py
```

You'll be prompted to:
1. Run a demo query (battery technology for EVs)
2. Enter interactive mode for multiple queries

### Single Query Mode

Pass your research question as an argument:

```bash
uv run deep_research_assistant.py "What are the latest advances in battery technology for electric vehicles?"
```

## Example Conversation

```
Research Query: What are the latest advances in quantum computing?

## Research Brief: Quantum Computing Advances

### Executive Summary
Recent breakthroughs in quantum error correction and hardware stability have pushed 
quantum computing closer to practical applications...

### Topic Overview
Quantum computing leverages quantum mechanical phenomena like superposition and 
entanglement to perform computations...

### Recent Developments
- IBM announced a 1,121-qubit processor "Condor"
- Google achieved quantum supremacy milestone...

### Key Research & Papers
- "Logical qubit demonstration using trapped ions" - Nature Physics
- "Quantum error correction threshold exceeded" - Science...

### Tools & Implementations
- Qiskit - IBM's open-source quantum computing framework
- Cirq - Google's quantum computing library...

### Sources
[URLs organized by search category]
```

## Project Structure

```
exa/
├── deep_research_assistant.py   # Main agent with Exa tool integration
├── .prompt                      # System prompt defining research workflow
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── requirements.txt            # Python dependencies (pip)
├── pyproject.toml              # Project dependencies (uv)
└── README.md                   # This file
```

## Dependencies

- **strands-agents** - AWS Strands Agents framework
- **strands-agents-tools** - Exa tools integration (exa_search, exa_get_contents)
- **boto3** - AWS SDK for Bedrock integration

## Resources

- [Strands Agents SDK](https://strandsagents.com)
- [Exa API Documentation](https://docs.exa.ai)
- [AWS Bedrock](https://aws.amazon.com/bedrock/)
- [Exa Dashboard](https://dashboard.exa.ai)

## License

Apache License 2.0
