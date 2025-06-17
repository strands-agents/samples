#!/usr/bin/env python3
"""
Financial Metrics Analysis Tool

A command-line tool that uses the Strands Agent SDK to analyze financial metrics of stocks.
"""

import datetime as dt
from typing import Dict, Union

# Third-party imports
import yfinance as yf
from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from strands_tools import think, http_request


@tool
def get_financial_metrics(ticker: str) -> Union[Dict, str]:
    """Fetches key financial metrics for a given stock ticker."""
    try:
        if not ticker.strip():
            return {"status": "error", "message": "Ticker symbol is required"}

        stock = yf.Ticker(ticker)
        info = stock.info

        # Get financial data
        try:
            metrics = {
                "status": "success",
                "data": {
                    "symbol": ticker,
                    "market_cap": info.get("marketCap", "N/A"),
                    "pe_ratio": info.get("trailingPE", "N/A"),
                    "forward_pe": info.get("forwardPE", "N/A"),
                    "peg_ratio": info.get("pegRatio", "N/A"),
                    "price_to_book": info.get("priceToBook", "N/A"),
                    "dividend_yield": info.get("dividendYield", "N/A"),
                    "profit_margins": info.get("profitMargins", "N/A"),
                    "revenue_growth": info.get("revenueGrowth", "N/A"),
                    "debt_to_equity": info.get("debtToEquity", "N/A"),
                    "return_on_equity": info.get("returnOnEquity", "N/A"),
                    "current_ratio": info.get("currentRatio", "N/A"),
                    "beta": info.get("beta", "N/A"),
                    "date": dt.datetime.now().strftime("%Y-%m-%d"),
                },
            }

            # Convert values to percentages where appropriate
            for key in [
                "dividend_yield",
                "profit_margins",
                "revenue_growth",
                "return_on_equity",
            ]:
                if (
                    isinstance(metrics["data"][key], (int, float))
                    and metrics["data"][key] != "N/A"
                ):
                    metrics["data"][key] = round(metrics["data"][key] * 100, 2)

            return metrics

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error processing financial data: {str(e)}",
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error fetching financial metrics: {str(e)}",
        }


def create_initial_messages():
    """Create initial conversation messages."""
    return [
        {
            "role": "user",
            "content": [
                {"text": "Hello, I need help analyzing company financial metrics."}
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "text": "I'm ready to help you analyze financial metrics. Please provide a company ticker symbol."
                }
            ],
        },
    ]


def create_financial_metrics_agent():
    """Create and configure the financial metrics analysis agent."""
    return Agent(
        system_prompt="""You are a financial analysis specialist. Follow these steps:

<input>
When user provides a company ticker:
1. Use get_financial_metrics to fetch data
2. Analyze key financial metrics
3. Provide comprehensive analysis in the format below
</input>

<output_format>
1. Company Overview:
   - Market Cap
   - Beta
   - Key Ratios

2. Valuation Metrics:
   - P/E Ratio
   - PEG Ratio
   - Price to Book

3. Financial Health:
   - Profit Margins
   - Debt Metrics
   - Growth Indicators

4. Investment Metrics:
   - Dividend Information
   - Return on Equity
   - Risk Assessment
</output_format>""",
        model=BedrockModel(model_id="us.amazon.nova-pro-v1:0", region="us-east-1"),
        tools=[get_financial_metrics, http_request, think],
    )


def main():
    """Main function to run the financial metrics analysis tool."""
    # Create and initialize the agent
    financial_metrics_agent = create_financial_metrics_agent()
    financial_metrics_agent.messages = create_initial_messages()

    print("\n📊 Financial Metrics Analyzer 📊\n")

    while True:
        query = input("\nEnter ticker symbol> ").strip()

        if query.lower() == "exit":
            print("\nGoodbye! 👋")
            break

        print("\nAnalyzing...\n")

        try:
            # Create the user message with proper Nova format
            user_message = {
                "role": "user",
                "content": [
                    {"text": f"Please analyze the financial metrics for: {query}"}
                ],
            }

            # Add message to conversation
            financial_metrics_agent.messages.append(user_message)

            # Get response
            response = financial_metrics_agent(user_message["content"][0]["text"])
            print(f"Analysis Results:\n{response}\n")

        except Exception as e:
            print(f"Error: {str(e)}\n")
        finally:
            # Reset conversation after each query
            financial_metrics_agent.messages = create_initial_messages()


if __name__ == "__main__":
    main()
