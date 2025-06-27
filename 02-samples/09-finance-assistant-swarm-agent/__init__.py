"""
Stock Analysis Tools

A collection of tools for analyzing stocks using the Strands Agent SDK.
"""

# Import modules
from . import stock_price_agent
from . import financial_metrics_agent
from . import company_analysis_agent
from . import finance_assistant_swarm_agent

# Import specific functions and classes for convenience
from .stock_price_agent import get_stock_prices, create_stock_price_agent
from .financial_metrics_agent import (
    get_financial_metrics,
    create_financial_metrics_agent,
)
from .company_analysis_agent import (
    get_company_info,
    get_stock_news,
    create_company_analysis_agent,
)
from .finance_assistant_swarm_agent import (
    StockAnalysisSwarm,
    create_orchestration_agent,
)

__all__ = [
    # Modules
    "stock_price_agent",
    "financial_metrics_agent",
    "company_analysis_agent",
    "finance_assistant_swarm_agent",
    # Functions
    "get_stock_prices",
    "get_financial_metrics",
    "get_company_info",
    "get_stock_news",
    # Agent creators
    "create_stock_price_agent",
    "create_financial_metrics_agent",
    "create_company_analysis_agent",
    "create_orchestration_agent",
    # Classes
    "StockAnalysisSwarm",
]
