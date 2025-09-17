# 🔍 Brave Web Search Assistant

## Overview

A comprehensive web search assistant powered by Brave Search API that provides intelligent web search capabilities through natural language conversations. Built with Strands Agents and Model Context Protocol (MCP) integration.

|Feature             |Description                                        |
|--------------------|---------------------------------------------------|
|Agent Structure     |Single agent with MCP tools                       |
|MCP Server          |[@modelcontextprotocol/server-brave-search](https://www.npmjs.com/package/@modelcontextprotocol/server-brave-search)|
|Search Types        |Web search, Local business search                 |
|Model Provider      |Amazon Bedrock (configurable)                     |
|API Integration     |Brave Search API                                   |

## 🌟 Key Features

### 🌐 Web Search
- Comprehensive web search across the internet
- Intelligent query processing and enhancement
- Result analysis and summarization
- Source citations and references

### 📍 Local Search  
- Find local businesses and places
- Location-based query detection
- Business information and reviews

### 🎯 Advanced Filtering
- Site-specific search (e.g., `site:github.com`)
- Content type filtering
- Freshness and relevance controls

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js and npm (for MCP server)
- [Brave Search API Key](https://api.search.brave.com/) (free tier available)
- Strands Agents installed

### Installation

1. **Navigate to the sample directory**:
```bash
cd 02-samples/14-brave-web-search-assistant
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env and add your Brave Search API key
```

4. **Run the assistant**:
```bash
python main.py
```

## 💡 Usage Examples

```
You: Search for recent AWS Lambda updates
🤖 Assistant: I'll search for recent AWS Lambda updates...

You: Find pizza restaurants near Central Park
🤖 Assistant: Let me search for pizza places near Central Park...

You: Search for Python tutorials on site:github.com
🤖 Assistant: I'll search for Python tutorials specifically on GitHub...
```

## 🔧 Configuration

### Environment Variables
- `BRAVE_API_KEY`: Your Brave Search API key (required)

### Brave Search API
- **Free Tier**: 2,000 queries per month
- **Paid Plans**: Higher limits and additional features
- **Sign up**: [https://api.search.brave.com/](https://api.search.brave.com/)

## 🏗️ Architecture

The assistant uses:
- **Strands Agent**: Core conversational AI framework
- **Brave Search MCP**: Model Context Protocol integration
- **NPX Server**: `@modelcontextprotocol/server-brave-search`
- **Query Processing**: Intelligent search optimization

## 📝 Sample Queries

- "What are the latest developments in artificial intelligence?"
- "Find coffee shops with good reviews in Seattle"
- "Search for AWS documentation on Lambda functions"
- "Look for recent news about climate change"
- "Find restaurants near Times Square New York"

## 🤝 Related Samples

- [AWS Assistant MCP](../03-aws-assistant-mcp/) - AWS-focused assistant with MCP
- [Personal Assistant](../05-personal-assistant/) - Multi-agent productivity assistant
- [Startup Advisor MCP](../04-startup-advisor-mcp/) - Business advisory with MCP tools

## 📚 Learn More

- [Strands Agents Documentation](https://strandsagents.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Brave Search API Documentation](https://api.search.brave.com/app/documentation/web-search/get-started)
