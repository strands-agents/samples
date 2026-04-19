#!/usr/bin/env python3
"""
Finance Assistant Swarm Agent

A collaborative swarm of specialized agents for comprehensive stock analysis.
"""
# Standard library imports
import logging
import re
import time
from typing import Dict, Any, List

# Third-party imports
from strands import Agent, tool
from strands.models import BedrockModel
from strands.multiagent import Swarm
from strands_tools import think
import yfinance as yf

from stock_price_agent import get_stock_prices, create_stock_price_agent
from financial_metrics_agent import get_financial_metrics, create_financial_metrics_agent
from company_analysis_agent import get_company_info, get_stock_news, create_company_analysis_agent

# Enable debug logs
logging.getLogger("strands.multiagent").setLevel(logging.DEBUG)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

@tool
def get_real_stock_data(ticker: str) -> Dict[str, Any]:
    """Get accurate stock data outside the swarm"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="5d")
        
        if hist.empty:
            return {"status": "error", "message": f"No data found for {ticker}"}
        
        current_price = round(float(hist["Close"].iloc[-1]), 2)
        prev_close = round(float(hist["Close"].iloc[-2]), 2) if len(hist) > 1 else current_price
        price_change = round(current_price - prev_close, 2)
        price_change_pct = round((price_change / prev_close) * 100, 2) if prev_close != 0 else 0
        
        return {
            "status": "success",
            "ticker": ticker.upper(),
            "current_price": current_price,
            "price_change": price_change,
            "price_change_pct": price_change_pct,
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "52_week_high": info.get("fiftyTwoWeekHigh"),
            "52_week_low": info.get("fiftyTwoWeekLow"),
            "volume": int(hist["Volume"].iloc[-1]),
            "revenue": info.get("totalRevenue"),
            "employees": info.get("fullTimeEmployees"),
            "sector": info.get("sector"),
            "industry": info.get("industry")
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def _extract_ticker(query: str) -> str:
    """Extract a stock ticker symbol from a query string.

    Handles cases like 'ALK', 'Analyze ALK', 'ALK (Alaska Air Group)', etc.
    """
    # If the query itself is already a short ticker, use it directly
    stripped = query.strip().upper()
    if re.fullmatch(r"[A-Z]{1,5}", stripped):
        return stripped

    # Try to find a 1-5 letter uppercase word that looks like a ticker
    match = re.search(r"\b([A-Z]{1,5})\b", query.upper())
    if match:
        return match.group(1)

    return stripped[:5] if stripped else "UNKNOWN"


# Model used for the swarm agents — using Opus for highest quality.
# Switch to a faster model like Haiku or Sonnet if you hit timeouts.
SWARM_MODEL_ID = "us.anthropic.claude-opus-4-6-v1"

# Model used for the orchestration agent (deep synthesis).
ORCHESTRATOR_MODEL_ID = "us.anthropic.claude-opus-4-6-v1"


@tool
def analyze_company_with_collaborative_swarm(ticker: str) -> Dict[str, Any]:
    """Run a collaborative swarm analysis for a stock ticker symbol (e.g. 'ALK', 'AAPL', 'MSFT').
    The ticker parameter must be a valid stock ticker symbol, not a full sentence."""
    try:
        ticker = _extract_ticker(ticker)

        company_strategist = Agent(
            name="company_strategist",
            system_prompt=f"Analyze {ticker} business model. Use get_company_info with ticker '{ticker}', then hand off to financial_analyst.",
            model=BedrockModel(model_id=SWARM_MODEL_ID),
            tools=[get_company_info]
        )

        financial_analyst = Agent(
            name="financial_analyst",
            system_prompt=f"Build on the company insights for {ticker}. Use get_financial_metrics with ticker '{ticker}', then hand off to market_analyst.",
            model=BedrockModel(model_id=SWARM_MODEL_ID),
            tools=[get_financial_metrics]
        )

        market_analyst = Agent(
            name="market_analyst",
            system_prompt=f"Synthesize all insights for {ticker}. Use get_stock_news with ticker '{ticker}' for final recommendation.",
            model=BedrockModel(model_id=SWARM_MODEL_ID),
            tools=[get_stock_news]
        )

        swarm = Swarm(
            [company_strategist, financial_analyst, market_analyst],
            max_handoffs=3,
            max_iterations=3,
            execution_timeout=300.0,
            node_timeout=90.0
        )
        
        result = swarm(f"Analyze {ticker}")
        
        return {
            "status": "success",
            "collaborative_analysis": result.final_response,
            "collaboration_path": [node.node_id for node in result.node_history]
        }
    except Exception as e:
        return {"status": "error", "collaborative_analysis": f"Analysis failed: {str(e)}"}

def create_orchestration_agent() -> Agent:
    """Orchestrator for deep synthesis"""
    return Agent(
        system_prompt="""You are a senior research director.

        WORKFLOW:
        1. Get real stock data using get_real_stock_data with the ticker symbol
        2. Get ONE collaborative analysis using analyze_company_with_collaborative_swarm — pass ONLY the ticker symbol (e.g. "ALK"), NOT a full sentence
        3. Synthesize using think tool for deep strategic insights

        CRITICAL RULES:
        - When calling analyze_company_with_collaborative_swarm, pass ONLY the stock ticker symbol (e.g. "ALK", "AAPL"), never a full sentence
        - DO NOT call analyze_company_with_collaborative_swarm multiple times
        - Focus on synthesis and strategic conclusions
        - Always prominently display the current stock price
        - Provide deep insights that demonstrate collaborative agent value

        REPORT STRUCTURE:
        1. Executive Summary (current price + key thesis)
        2. Strategic Business Analysis (from collaborative insights)
        3. Financial Health Assessment (integrated metrics)
        4. Market Sentiment Analysis (news + trends)
        5. Investment Recommendation (buy/hold/sell with rationale)""",
        model=BedrockModel(model_id=ORCHESTRATOR_MODEL_ID),
        tools=[get_real_stock_data, analyze_company_with_collaborative_swarm, think],
    )

def create_initial_messages() -> List[Dict]:
    """Create initial conversation messages."""
    return [
        {
            "role": "user",
            "content": [{"text": "Hello, I need help analyzing company stocks."}],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "text": "I'm ready to provide comprehensive stock analysis using real-time data and collaborative multi-agent analysis. Please provide a company name or ticker."
                }
            ],
        },
    ]

def main():
    """Main function to run the finance assistant swarm."""
    # Create the orchestration agent
    orchestration_agent = create_orchestration_agent()

    # Initialize messages for the orchestration agent
    orchestration_agent.messages = create_initial_messages()

    print("\n🤖 Hybrid Multi-Agent Stock Analysis 📊")
    print("Features: Real-time data + Fast collaborative swarm + Deep orchestrator synthesis\n")

    while True:
        query = input("\nWhat company would you like to analyze? (or 'exit' to quit)> ")

        if query.lower() == "exit":
            print("\nGoodbye! 👋")
            break

        print("\nInitiating hybrid collaborative analysis...\n")

        try:
            # Create the user message with proper Nova format
            user_message = {
                "role": "user",
                "content": [
                    {
                        "text": f"Please analyze {query} using real stock data and collaborative multi-agent analysis. Ensure agents build upon each other's insights and provide a comprehensive strategic analysis. Display the current stock price prominently."
                    }
                ],
            }

            # Add message to conversation
            orchestration_agent.messages.append(user_message)

            # Get response
            response = orchestration_agent(user_message["content"][0]["text"])

            # Format and print response
            if isinstance(response, dict) and "content" in response:
                print("\nHybrid Collaborative Analysis Results:")
                for content in response["content"]:
                    if "text" in content:
                        print(content["text"])
            else:
                print(f"\nHybrid Collaborative Analysis Results:\n{response}\n")

        except Exception as e:
            print(f"Error: {str(e)}\n")
            if "ThrottlingException" in str(e):
                print("Rate limit reached. Waiting 10 seconds before retry...")
                time.sleep(10)
                continue
        finally:
            # Reset conversation after each query to maintain clean context
            orchestration_agent.messages = create_initial_messages()
            
if __name__ == "__main__":
    main()
