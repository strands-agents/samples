#!/usr/bin/env python3
"""
Finance Assistant Swarm Agent

A collaborative swarm of specialized 02-agents for comprehensive stock analysis.
"""

# Standard library imports
import time
from typing import Dict, Any, List

# Third-party imports
from strands import Agent
from strands.models import BedrockModel
from strands_tools import think, http_request
from strands_tools.swarm import Swarm, SwarmAgent

from stock_price_agent import get_stock_prices, create_stock_price_agent
from financial_metrics_agent import (
    get_financial_metrics,
    create_financial_metrics_agent,
)
from company_analysis_agent import (
    get_company_info,
    get_stock_news,
    create_company_analysis_agent,
)


class StockAnalysisSwarm:
    """A collaborative swarm of specialized 02-agents for stock analysis."""

    def __init__(self):
        """Initialize the swarm with specialized 02-agents."""
        # Initialize Swarm with Nova Pro model
        self.swarm = Swarm(
            task="Analyze company stock with multiple specialized 02-agents",
            coordination_pattern="collaborative",
        )

        # Create SwarmAgent instances with correct parameters
        self.search_agent = SwarmAgent(
            agent_id="search_agent",
            system_prompt="""You are a company information specialist.
            Your role is to:
            1. Use get_company_info to find company details and ticker
            2. Verify company identity
            3. Share company information with other 02-agents
            4. Ensure accuracy of company data""",
            shared_memory=self.swarm.shared_memory,
        )
        self.search_agent.tools = [get_company_info, think]

        self.price_agent = SwarmAgent(
            agent_id="price_agent",
            system_prompt=create_stock_price_agent().system_prompt,  # Use the created agent's system prompt
            shared_memory=self.swarm.shared_memory,
        )
        self.price_agent.tools = [
            get_stock_prices,
            http_request,
            think,
        ]  # Set tools directly

        self.metrics_agent = SwarmAgent(
            agent_id="metrics_agent",
            system_prompt=create_financial_metrics_agent().system_prompt,
            shared_memory=self.swarm.shared_memory,
        )
        self.metrics_agent.tools = [get_financial_metrics, http_request, think]

        self.news_agent = SwarmAgent(
            agent_id="news_agent",
            system_prompt=create_company_analysis_agent().system_prompt,
            shared_memory=self.swarm.shared_memory,
        )
        self.news_agent.tools = [get_company_info, get_stock_news, http_request, think]

        # Add 02-agents to swarm with their system prompts
        self.swarm.add_agent(
            self.search_agent,
            system_prompt="""You are the company information coordinator in the swarm.
            Use get_company_info to find and verify company information.
            Share verified company data with other 02-agents.
            Focus on accuracy and completeness of information.""",
        )

        self.swarm.add_agent(
            self.price_agent,
            system_prompt="""You are a price analysis specialist in the swarm.
            Analyze stock prices, trends, and patterns.
            Share price analysis with other 02-agents.
            Focus on recent price movements and volume analysis.""",
        )

        self.swarm.add_agent(
            self.metrics_agent,
            system_prompt="""You are a financial metrics specialist in the swarm.
            Analyze company financial health and metrics.
            Share financial insights with other 02-agents.
            Focus on key performance indicators and growth metrics.""",
        )

        self.swarm.add_agent(
            self.news_agent,
            system_prompt="""You are a news analysis specialist in the swarm.
            Analyze company news and market sentiment.
            Share news insights with other 02-agents.
            Focus on recent developments and market perception.""",
        )

    def analyze_company(self, query: str) -> Dict[str, Any]:
        """Run the swarm analysis for a company."""
        try:
            # Initialize shared memory with query
            self.swarm.shared_memory.store("query", query)

            # Phase 1: Search for ticker
            print("\nPhase 1: Searching for company ticker...")
            search_result = self.swarm.process_phase()

            if search_result:
                ticker = (
                    search_result[0]
                    .get("result", {})
                    .get("content", [{}])[0]
                    .get("text", "")
                )
                self.swarm.shared_memory.store("ticker", ticker)
                print(f"Found ticker: {ticker}")

                # Phase 2: Parallel Analysis
                print("\nPhase 2: Gathering data...")
                analysis_results = self.swarm.process_phase()

                return {
                    "status": "success",
                    "ticker": ticker,
                    "search_results": search_result,
                    "analysis_results": analysis_results,
                    "shared_memory": self.swarm.shared_memory.get_all_knowledge(),
                }
            else:
                return {"status": "error", "message": "Failed to find ticker symbol"}

        except Exception as e:
            return {"status": "error", "message": str(e)}


def create_orchestration_agent() -> Agent:
    """Create the main orchestration agent that coordinates the swarm."""
    return Agent(
        system_prompt="""You are a stock analysis orchestrator and integrator. Your role is to:
        1. Coordinate the swarm of specialized 02-agents
        2. Monitor the analysis process
        3. Integrate and synthesize all findings
        4. Present a comprehensive analysis
        
        When analyzing results, structure the report as follows:
        1. Company Overview
           - Company name and ticker
           - Industry and sector
           - Basic business description
        
        2. Stock Price Analysis
           - Current price and recent changes
           - Price trends and patterns
           - Trading volume analysis
        
        3. Financial Health
           - Key financial metrics
           - Performance indicators
           - Growth metrics
        
        4. Market Sentiment
           - Recent news analysis
           - Market perception
           - Key developments
        
        5. Integrated Insights
           - Overall assessment
           - Key opportunities and risks
           - Future outlook
           - Recommendation summary""",
        model=BedrockModel(model_id="us.amazon.nova-pro-v1:0", region="us-east-1"),
        tools=[StockAnalysisSwarm().analyze_company, think, http_request],
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
                    "text": "I'm ready to help you analyze companies. Please provide a company name you'd like to analyze."
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

    print("\n🤖 Stock Analysis Swarm 📊\n")

    while True:
        query = input("\nWhat company would you like to analyze? (or 'exit' to quit)> ")

        if query.lower() == "exit":
            print("\nGoodbye! 👋")
            break

        print("\nInitiating swarm analysis...\n")

        try:
            # Create the user message with proper Nova format
            user_message = {
                "role": "user",
                "content": [
                    {
                        "text": f"Please analyze {query} and provide a comprehensive report integrating all findings."
                    }
                ],
            }

            # Add message to conversation
            orchestration_agent.messages.append(user_message)

            # Get response
            response = orchestration_agent(user_message["content"][0]["text"])

            # Format and print response
            if isinstance(response, dict) and "content" in response:
                print("\nAnalysis Results:")
                for content in response["content"]:
                    if "text" in content:
                        print(content["text"])
            else:
                print(f"\nAnalysis Results:\n{response}\n")

        except Exception as e:
            print(f"Error: {str(e)}\n")
            if "ThrottlingException" in str(e):
                print("Rate limit reached. Waiting 5 seconds before retry...")
                time.sleep(5)
                continue
        finally:
            # Reset conversation after each query to maintain clean context
            orchestration_agent.messages = create_initial_messages()


if __name__ == "__main__":
    main()
