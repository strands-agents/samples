# Finance-Assistant Swarm Agent Collaboration 📊 🐝

Author: Julia Hu

Finance-Assistant Swarm Agent Collaboration is a modular, multi-agent system designed to autonomously generate comprehensive equity research reports from a single stock query. Built using the Strands SDK and powered by Amazon Bedrock, this assistant orchestrates a collaborative swarm of specialized agents—each responsible for a distinct financial research task including ticker resolution, company profiling, price analytics, financial health assessment, and sentiment analysis.

By leveraging shared memory and coordinated agent workflows, the system transforms raw data from APIs and web sources into a polished, structured Markdown or HTML report. The orchestrator uses natural language reasoning and synthesis (via Amazon Nova) to integrate the findings into actionable insights. The architecture supports flexible deployment, modular agent execution, and scalable financial intelligence delivery for developers, analysts, and automated trading systems.

![Architecture](Image/architecture_stock_swarm.png)

## 1. What is this?

A modular swarm of agents that delivers a **holistic equity research report** from a single ticker symbol.

| Function | Agent | Data Source | Output |
|----------|-------|-------------|--------|
| **Orchestration** | `orchestration_agent` | Coordinates swarm & writes final report | Structured Markdown / HTML |
| **Discovery** | `ticker_search_agent` | Memory + Bedrock reasoning | Normalised ticker |
| **Company profile** | `company_info_agent` | Yahoo Finance _/companyInfo_ API | Name, sector, description |
| **Price analytics** | `stock_price_agent` | Yahoo Finance _/stockHistory_ API | OHLC, volume, trends |
| **Financial metrics** | `financial_metrics_agent` | Yahoo Finance _/companyFinancial_ API | Ratios & growth metrics |
| **Sentiment & news** | `news_agent` | Web search (DuckDuckGo/Bing) | Headlines, industry buzz |

## 2. Flow overview 🚦

1. **User** ➜ `orchestration_agent` with a plain-language stock question
2. Orchestrator calls `ticker_search_agent` → resolves correct ticker
3. Ticker is **broadcast** to specialised agents (shared memory)
4. Each agent pulls data, analyses, writes a _section draft_
5. Orchestrator **integrates & polishes** into one cohesive report using Amazon Nova
6. Final Markdown / HTML returned to the user (CLI, API, or chat UI)

## 3. Report format 📋

The orchestrator outputs five ordered sections:

1. **Company Overview** – name, ticker, sector, concise description
2. **Stock Price Analysis** – latest price, % move, trend charts, volume spike notes
3. **Financial Health** – revenue / EPS growth, margins, leverage, cash flow
4. **Market Sentiment** – headline heat-map, keyword cloud, notable events
5. **Integrated Insights** – strengths, risks, forward outlook, ↑/↓ triggers, recommendation

## 4. Quick start 🛠️ (local dev)

### Prerequisites

- Python 3.10+
- AWS CLI v2 configured
- [Access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html) to Amazon Bedrock (Nova in us-east-1 region)

### Running the Application

#### Run the swarm agent

```bash
uv run finance_assistant_swarm.py
```

#### Optional: Run individual agents

```bash
# Run the stock price agent
uv run stock_price_agent.py

# Run the financial metrics agent
uv run financial_metrics_agent.py

# Run the company analysis agent
uv run company_analysis_agent.py
```

## 5. AWS Architecture 🏗️ (components)

| Component Type | AWS Service | Description |
|----------------|-------------|-------------|
| Data Pipeline | Bedrock Data Automation | Converts raw Audio files → embeddable docs |
| Storage Layer | S3 | Durable store for documents & images |
| Search Layer | Amazon Bedrock Knowledge Base | Vector / keyword index for RAG_agent |
| AI Services | Amazon Nova | Foundation model for text + image generation |

## 6. Troubleshooting 🐞

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| **NoCredentialsError** | AWS credentials not exported | Run `aws configure --profile ...` |
| **Report Throttle** | FM inference request throttle | Consider Provision Throughput |
| **ImportError Strands SDK** | Missing Strands SDK | Check Python path |
| **ModuleNotFoundError** | Incorrect import structure | Check file path |
