# :bar_chart::bee: Finance-Assistant Swarm Agent Collaboration

Multi‑agent financial research powered by Strands SDK
![Architecture](Image/architecture_stock_swarm.png)

---

## 1. What is this?

A modular swarm of agents that delivers a **holistic equity research report** from a single ticker symbol.
| Function | Agent (:jigsaw:) | Data Source | Output |
|-------------------------|---------------------|-----------------------------|--------|
| **Orchestration** | `orchestration_agent` | Coordinates swarm & writes final report | Structured Markdown / HTML |
| **Discovery** | `ticker_search_agent` | Memory + Bedrock reasoning | Normalised ticker |
| **Company profile** | `company_info_agent` | Yahoo Finance _/companyInfo_ API | Name, sector, description |
| **Price analytics** | `stock_price_agent` | Yahoo Finance _/stockHistory_ API | OHLC, volume, trends |
| **Financial metrics** | `financial_metrics_agent` | Yahoo Finance _/companyFinancial_ API | Ratios & growth metrics |
| **Sentiment & news** | `news_agent` | Web search (DuckDuckGo/Bing) | Headlines, industry buzz |

---

## 2. Flow overview :vertical_traffic_light:

**User** ➜ `orchestration_agent` with a plain‑language stock question
Orchestrator calls `ticker_search_agent` → resolves correct ticker
Ticker is **broadcast** to specialised agents (shared memory)
Each agent pulls data, analyses, writes a _section draft_
Orchestrator **integrates & polishes** into one cohesive report using Amazon Nova
Final Markdown / HTML returned to the user (CLI, API, or chat UI)

## 3. Report format :card_index_dividers:

The orchestrator outputs five ordered sections:
Company Overview – name, ticker, sector, concise description
Stock Price Analysis – latest price, % move, trend charts, volume spike notes
Financial Health – revenue / EPS growth, margins, leverage, cash flow
Market Sentiment – headline heat‑map, keyword cloud, notable events
Integrated Insights – strengths, risks, forward outlook, :arrow_up:/:arrow_down: triggers, recommendation

---

finance-assistant-swarm-agent/
├── **init**.py # Package initialization
├── requirements.txt # Project dependencies
├── stock_price_agent.py # Stock price analysis agent
├── financial_metrics_agent.py # Financial metrics analysis agent
├── company_analysis_agent.py # Company info and news analysis agent
├── finance_assistant_swarm_agent.py # Main swarm orchestration agent
└── Image/ # Images and diagrams
└── architecture_stock_swarm.png # Architecture diagram

## 5. Quick start (:hammer_and_wrench: local dev)

**Prerequisites**
• Python 3.10+ • AWS CLI v2 configured
• Access to Amazon Bedrock (Nova Por in us-east-1 region)

# 1. Clone the repository

git clone https://github.com/strands-agents/agents-samples.git
cd agents-samples/03-multi-agent-collaboration/01-finance-assistant-swarm-agent

# 2. Create and activate a virtual environment

python -m venv .venv
source .venv/bin/activate # On Windows: .venv\Scripts\activate

# 3. Install dependencies

pip install -r requirements.txt

# 4. Run the swarm python file:

Running the Swarm Agent
python -m finance_assistant_swarm_agent

# 5. Optional: you can run individual agent:

# Run the stock price agent

python -m stock_price_agent

# Run the financial metrics agent

python -m financial_metrics_agent

# Run the company analysis agent

python -m company_analysis_agent

## 6. AWS Architecture (:building_construction: components)

Component Type/ AWS Service/  
Data Pipeline Bedrock Data Automation (Converts raw Audio files → embeddable docs)
Storage Layer S3 Durable store for documents & images
Search Layer Amazon Bedrock Knowledge Base (Vector / keyword index for RAG_agent)
AI Services Amazon Nova Foundation model for text + image generation

## 7. Troubleshooting :ladybug:

| Symptom                     | Likely Cause                  | Fix                             |
| --------------------------- | ----------------------------- | ------------------------------- |
| **NoCredentialsError**      | AWS credentials not exported  | Run aws configure --profile ... |
| **Report Throttle**         | FM inference request throttle | Consider Provision Throughput   |
| **ImportError Strands SDK** | Missing Strands SDK           | Check Python path               |
| **ModuleNotFoundError**     | Incorrect import structure    | Check file path                 |
