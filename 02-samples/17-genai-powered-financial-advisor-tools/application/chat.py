#This sample application is intended solely for educational and knowledge-sharing purposes. It is not designed to provide investment guidance or financial advice.

import asyncio
import logging
import os
import re
import sys
import traceback

import nest_asyncio
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from botocore.config import Config
from mcp import StdioServerParameters, stdio_client
from pydantic import BaseModel, Field
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from strands import Agent, tool
from strands_tools import retrieve
from strands.models import BedrockModel
from strands.multiagent import GraphBuilder
from strands.tools.mcp import MCPClient

import info
import prompt

model_name = "Claude 3.7 Sonnet"
reasoning_mode = "Disable"
os.environ["BYPASS_TOOL_CONSENT"] = "true"  # Bypass consent for file_write

# Global variable to store chart image path for Streamlit display
chart_image_path = None

logging.basicConfig(
    level=logging.INFO,  
    format="%(filename)s:%(lineno)d | %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("chat")

# Load prereqs_config.yaml data
def load_config():
    """Load configuration from prereqs_config.yaml"""
    config_path = Path(__file__).parent / "prerequisites" / "prereqs_config.yaml"
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            #logger.info(f"✅ Loaded config with {len(config)} keys")
            return config
    except Exception as e:
        logger.warning(f"❌Could not load config from {config_path}: {e}")
        return {}

def update(modelName, reasoningMode):
    global model_name, reasoning_mode

    if model_name != modelName:
        model_name = modelName
        logger.info(f"model_name: {model_name}")

    if reasoningMode != reasoning_mode:
        reasoning_mode = reasoningMode
        logger.info(f"reasoning_mode: {reasoning_mode}")

# ============================================================================
# Strands Agent Model Configuration
# ============================================================================
def get_model():
    # Get fresh model info based on current model_name
    models = info.get_model_info(model_name)
    if not models:
        raise ValueError(f"No model configuration found for: {model_name}")
    
    profile = models[0]
    model_type = profile["model_type"]
    model_id = profile["model_id"]
    
    if model_type == "nova":
        STOP_SEQUENCE = '"\n\n<thinking>", "\n<thinking>", " <thinking>"'
    elif model_type == "claude":
        STOP_SEQUENCE = "\n\nHuman:"

    if model_type == "claude":
        maxOutputTokens = 64000  
    else:
        maxOutputTokens = 5120  

    maxReasoningOutputTokens = 64000
    thinking_budget = min(maxOutputTokens, maxReasoningOutputTokens - 1000)

    if reasoning_mode == "Enable":
        # Configure thinking parameters
        thinking_config = {
            "type": "enabled",
            "budget_tokens": thinking_budget,
        }

        additional_fields = {"thinking": thinking_config}

        if model_name in ["Claude 4 Sonnet", "Claude 3.7 Sonnet"]:
            additional_fields["anthropic_beta"] = ["interleaved-thinking-2025-05-14"]

        model = BedrockModel(
            boto_client_config=Config(
                read_timeout=900,
                connect_timeout=900,
                retries=dict(max_attempts=3, mode="adaptive"),
            ),
            model_id=model_id,
            max_tokens=64000,
            stop_sequences=[STOP_SEQUENCE],
            temperature=1,
            additional_request_fields=additional_fields,
        )
    else:
        model = BedrockModel(
            boto_client_config=Config(
                read_timeout=900,
                connect_timeout=900,
                retries=dict(max_attempts=3, mode="adaptive"),
            ),
            model_id=model_id,
            max_tokens=maxOutputTokens,
            stop_sequences=[STOP_SEQUENCE],
            temperature=0.1,
            #top_p=0.9,
            additional_request_fields={"thinking": {"type": "disabled"}},
        )
    return model

# ============================================================================
# MCP Clients for various scientific databases
# ============================================================================
kb_mcp_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="python", args=["application/mcp_server_kb.py"]
        )
    )
)

tavily_mcp_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="python", args=["application/mcp_server_tavily.py"]
        )
    )
)

athena_mcp_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="python", args=["application/mcp_server_athena.py"]
        )
    )
)

stock_mcp_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="python", args=["application/mcp_server_stock.py"]
        )
    )
)

# ============================================================================
# A specialized agent for client meeting analysis based on Amazon Bedrock Knowledge Bases ID.
# ============================================================================
INVALID_KB_IDS = {"<UNKNOWN>", "UNKNOWN", "NULL", "NONE", "N/A"}
MIN_KB_ID_LENGTH = 3

class knowledge_base_id_extraction(BaseModel):
    """Knowledge base ID extraction model"""
    knowledge_base_id: Optional[str] = Field(
        default=None,
        description="Knowledge base ID, kb id, or kb identifier. Only extract if explicitly mentioned. Return None if not found."
    )

def get_kb_id(query: Optional[str] = None) -> Tuple[Optional[str], str]:
    """
    Get knowledge base ID from query or config with validation.
    
    Args:
        query: Optional query string to extract KB ID from
        
    Returns:
        Tuple of (kb_id, source) where source is 'query', 'config', or None
    """
    def is_valid(kb_id: str) -> bool:
        """Validate KB ID format"""
        if not kb_id or len(kb_id) < MIN_KB_ID_LENGTH:
            return False
        kb_upper = kb_id.upper().strip()
        return (kb_upper not in INVALID_KB_IDS and 
                not kb_id.startswith("<") and 
                not kb_id.endswith(">"))
    
    if query and query.strip():
        try:
            extraction_agent = Agent(name="kb_id_extraction_agent")
            result = extraction_agent.structured_output(knowledge_base_id_extraction, query)
            
            if result and result.knowledge_base_id:
                kb_id = result.knowledge_base_id.strip()
                if is_valid(kb_id):
                    logger.info(f"✅ Valid KB ID from query: {kb_id}")
                    return kb_id, "query"
                logger.info(f"⚠️ Invalid KB ID from query: {kb_id}")
        except Exception as e:
            logger.warning(f"KB ID extraction failed: {e}")
    
    try:
        config = load_config()
        kb_id = config.get("knowledge_base_id", "").strip()
        
        if is_valid(kb_id):
            #logger.info(f"✅ Valid KB ID from config: {kb_id}")
            return kb_id, "config"
        logger.error(f"❌ Invalid config KB ID: '{kb_id}'")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
    
    return None, None

def extract_kb_id_from_query(query: str) -> Optional[str]:
    """Extract KB ID from query only (for backward compatibility)"""
    kb_id, source = get_kb_id(query)
    return kb_id if source == "query" else None

def get_kb_id_from_config() -> Optional[str]:
    """Get KB ID from config only (for backward compatibility)"""
    kb_id, source = get_kb_id(None)
    return kb_id if source == "config" else None

@tool
def client_meeting_analysis(query: str) -> str:
    """
    Advanced client meeting analysis agent for comprehensive meeting note processing and sentiment analysis.
    
    This agent extracts and analyzes client meeting information from knowledge bases, providing
    structured insights including sentiment assessment, key decisions, and actionable items.

    Args:
        query (str): Analysis request containing the knowledge base ID and specific analysis requirements.
        
    Returns:
        str: Comprehensive meeting analysis containing:
        - Meeting summary with key discussion points
        - Customer sentiment assessment with supporting evidence based on timeline
        - Negative feedback highlighted in red font: <span style="color:red; font-weight:bold">"feedback text"</span>
        - Positive feedback highlighted in red font: <span style="color:blue; font-weight:bold">"feedback text"</span> 
        - Key decisions made during the meeting
        - Action items for follow-up

    Raises:
        Returns error message string if knowledge base unavailable or analysis fails
    """
    if not query or not query.strip():
        return "Error: Meeting analysis query cannot be empty."
    
    sanitized_query = query.strip()
    if len(sanitized_query) > 2000:
        return "Error: Query too long. Please limit to 2000 characters."

    try:
        logger.info(f"🔍 Resolving KB ID from query: '{sanitized_query[:50]}...'")
        kb_id, kb_source = get_kb_id(sanitized_query)
        
        if not kb_id:
            return "Error: No valid knowledge base ID found in query or config. Please provide KB ID in query or configure it in prereqs_config.yaml."
        
        logger.info(f"📋 Using KB ID: {kb_id} (source: {kb_source})")

        os.environ.update({
            "BYPASS_TOOL_CONSENT": "true", 
            "KNOWLEDGE_BASE_ID": kb_id
        })
        
        model = get_model()
        if not model:
            return "Error: Meeting analysis model unavailable."

        meeting_agent = Agent(
            model=model,
            system_prompt=prompt.customer_meeting_analysis_agent_prompt,
            tools=[retrieve]
        )
        
        logger.info(f"🚀 Executing meeting analysis with KB: {kb_id}")
        
        response = meeting_agent(sanitized_query)
        
        if not response:
            return "Error: No analysis results returned. Please verify KB contains meeting notes."
        
        logger.info(f"✅ Meeting analysis completed successfully")
        return str(response)

    except Exception as e:
        error_msg = f"Meeting analysis error: {str(e)}"
        logger.error(error_msg)
        return f"Error: Analysis failed. Please verify KB ID and try again. Details: {str(e)}"

# ============================================================================
# A specialized agent for searching web using Tavily MCP
# ============================================================================
@tool
def web_search_agent(query: str, search_type: str = "general") -> str:
    """
    Advanced web search agent utilizing Tavily to retrieve comprehensive, accurate information from the internet.
    
    This agent provides intelligent web research capabilities for financial advisors, delivering structured,
    compliant results that adhere to professional standards and regulatory requirements.

    Args:
        query (str): The search query or question to research. Should be specific and well-formed.
        search_type (str): Type of search to perform. Options:
            - "general": Comprehensive search across multiple sources (default)
            - "news": Focus on recent news and current events
            - "answer": Direct answer-focused search for specific questions

    Returns:
        str: Structured response containing:
            - Comprehensive search findings with key insights
            - Source citations with publication dates and hyperlinks
            - Regulatory compliance considerations when applicable
            - Risk factors and limitations identified
            - Professional disclaimers and data verification status

    Raises:
        Returns error message string if client unavailable or search fails
    """
    if not query or not query.strip():
        return "Error: Search query cannot be empty. Please provide a specific question or search term."
    
    valid_search_types = ["general", "news", "answer"]
    if search_type.lower() not in valid_search_types:
        logger.warning(f"Invalid search_type '{search_type}', defaulting to 'general'")
        search_type = "general"
    
    client = _session_manager.get_client("tavily")
    if client is None:
        error_msg = "Error: Tavily web search service is currently unavailable. Please try again later."
        logger.error("Tavily client session not available in session manager")
        return error_msg

    try:
        tavily_tools = client.list_tools_sync()
        if not tavily_tools:
            error_msg = "Error: Web search tools are currently unavailable. Please contact support if this persists."
            logger.error("Tavily client session has no available tools")
            return error_msg

        logger.info(f"Web search initiated - Query: '{query[:50]}...', Type: {search_type}, Tools: {len(tavily_tools)}")

        model = get_model()
        if not model:
            error_msg = "Error: Search model configuration unavailable. Please try again."
            logger.error("Failed to get model configuration for web search agent")
            return error_msg

        web_agent = Agent(
            name="web_search_agent",
            model=model,
            system_prompt=prompt.web_search_prompt, 
            tools=tavily_tools
        )

        enhanced_query = _enhance_search_query(query, search_type)
        
        logger.info(f"Executing web search with enhanced query: '{enhanced_query[:100]}...'")

        response = web_agent(enhanced_query)
        
        if not response:
            return "Error: Search completed but no results were returned. Please try rephrasing your query."
        
        logger.info(f"Web search completed successfully for query: '{query[:50]}...'")
        
        return str(response)

    except Exception as e:
        error_msg = f"Error during web search execution: {str(e)}"
        logger.error(f"Web search agent error - Query: '{query}', Error: {error_msg}")
        
        return (
            "Error: An issue occurred while searching the web. This could be due to "
            "network connectivity, service availability, or query complexity. "
            "Please try again with a simpler query or contact support if the issue persists."
        )

def _enhance_search_query(query: str, search_type: str) -> str:
    """
    Enhance search query based on search type for optimal results.
    
    Args:
        query: Original search query
        search_type: Type of search being performed
        
    Returns:
        Enhanced query string optimized for the specified search type
    """
    query = query.strip()
    
    if search_type.lower() == "news":
        enhanced_query = f"RECENT NEWS AND CURRENT EVENTS: {query}"
        if "recent" not in query.lower() and "latest" not in query.lower():
            enhanced_query += " (focus on latest developments and recent updates)"
            
    elif search_type.lower() == "answer":
        enhanced_query = f"PROVIDE DIRECT ANSWER: {query}"
        if "?" not in query:
            enhanced_query += " - provide specific, factual answer with sources"
            
    else:  # general search

        enhanced_query = f"COMPREHENSIVE RESEARCH: {query}"
        enhanced_query += " (provide detailed analysis with multiple perspectives and sources)"
    
    return enhanced_query

# ============================================================================
# A specialized agent for searching available knowledge bases by utilizing Amazon Bedrock Knowledge Bases MCP
# ============================================================================
@tool
def knowledge_bases_agent(query: str) -> str:
    """
    Specialized agent for retrieving knowledge base list on Amazon Bedrock for financial advisor

    Args:
        query: The search query for Knowledge base

    Returns:
        response from the MCP server
    """
    if not query or not query.strip():
        return "Error: Knowledge base query cannot be empty. Please provide a specific search term or question."

    client = _session_manager.get_client("kb")
    if client is None:
        error_msg = "Error: Active kb client session is required but not provided"
        logger.error(error_msg)
        return error_msg

    try:
        kb_tools = client.list_tools_sync()
        if not kb_tools:
            error_msg = (
                "Error: KB client session is invalid or has no available tools"
            )
            logger.error(error_msg)
            return error_msg

        logger.info(f"kb_tools: {kb_tools}")

        kb_system_prompt = """
            Specialized agent for returning list of Bedrock Knowledge Bases
            """
        model = get_model()

        kb_agent = Agent(name="knowledge_bases_agent", model=model, system_prompt=kb_system_prompt, tools=kb_tools)

        response = kb_agent(query)
        return str(response)
    
    except Exception as e:
        error_msg = f"Error in kb research agent: {str(e)}"
        logger.error(error_msg)
        return error_msg

# ============================================================================
# A specialized agent for querying database via Amazon Athena MCP
# ============================================================================
@tool
def database_query_agent(query: str) -> str:
    """
    This function acts as a specialized agent designed to search and retrieve various types of investment-related data. 
    It can query advisors, client information, performance metrics, portfolio holdings, portfolio details, and securities data.

    Args:
        query (str): The search query string used to fetch investment data.

    Returns:
        str: A summarized report of the findings obtained from the executed Athena query.
            If the response includes a portfolio overview, it will be summarized in bullet point format.
            If the response includes portfolio holdings and securities data, it will be displayed in a table format.
            If the response includes performance returns, they will be displayed in a table format.
            If the response includes underlying assets such as securities, they will be displayed in a table format.
            If portfolio return is included, provide summary of overall investments.
    """
    if not query or not query.strip():
        return "Error: Database query cannot be empty. Please provide a specific search query for investment data."
    
    sanitized_query = query.strip()
    if len(sanitized_query) > 1000:  # Reasonable limit for database queries
        return "Error: Query too long. Please limit database queries to 1000 characters."

    client = _session_manager.get_client("database")
    if client is None:
        error_msg = "Error: Database client session not available"
        logger.error("Database client session not available in session manager")
        return error_msg

    try:
        database_tools = client.list_tools_sync()
        if not database_tools:
            error_msg = (
                "Error: Database Query client session is invalid or has no available tools"
            )
            logger.error(error_msg)
            return error_msg

        logger.info(f"Database query initiated - Query: '{sanitized_query[:50]}...', Tools: {len(database_tools)}")

        model = get_model()
        if not model:
            error_msg = "Error: Database query model configuration unavailable. Please try again."
            logger.error("Failed to get model configuration for database agent")
            return error_msg

        db_prompt = prompt.get_database_query_prompt()
        
        database_agent = Agent(
            name="database_query_agent",
            model=model, 
            system_prompt=db_prompt, 
            tools=database_tools
        )
        
        logger.info(f"Executing database query: '{sanitized_query}'")

        response = database_agent(sanitized_query)
        
        if not response:
            return "Error: Database query completed but no results were returned. Please verify your query parameters and try again."
        
        logger.info(f"Database query completed successfully for: '{sanitized_query[:50]}...'")
        
        return str(response)
        
    except Exception as e:
        error_msg = f"Error in database query agent: {str(e)}"
        logger.error(f"Database agent error - Query: '{sanitized_query}', Error: {error_msg}")

        return (
            "Error: An issue occurred during database query execution. This could be due to "
            "database connectivity, query syntax, or data access permissions. "
            "Please verify your query and try again, or contact support if the issue persists."
        )

# ============================================================================
# A specialized agent for searching stock data using yahoo finance MCP
# ============================================================================
@tool
def stock_agent(query: str, search_type: str = "general") -> str:
    """ 
    Specialized stock data agent for comprehensive equity market analysis and financial metrics.
    
    Provides real-time and historical stock data, financial metrics, pricing information,
    and market analysis to support investment decision-making and portfolio management.

    Args:
        query (str): Stock ticker symbol or analysis request. Examples:
            - "AAPL" (for Apple Inc. current data)
            - "TSLA historical pricing last 6 months"
            - "MSFT financial metrics and ratios"
            - "SPY price and volume data"
        search_type (str): Type of stock analysis to perform. Options:
            - "general": Comprehensive stock analysis (default)
            - "pricing": Focus on current and historical pricing data
            - "metrics": Focus on financial metrics and ratios
            - "chart": Generate stock charts and comparison charts

    Returns:
        str: Comprehensive stock information containing:
            - Current stock pricing and market data
            - Historical pricing trends and patterns
            - Financial metrics and key ratios
            - Volume analysis and trading information
            - Market performance comparisons
            - Charts and visualizations when requested
            - Display the data in table format if it is comparison data

    Raises:
        Returns error message string if stock service unavailable or query fails
    """
    if not query or not query.strip():
        return "Error: Stock query cannot be empty. Please provide a stock ticker symbol or analysis request."
    
    sanitized_query = query.strip()
    if len(sanitized_query) > 500:  # Reasonable limit for stock queries
        return "Error: Query too long. Please limit stock analysis requests to 500 characters."
    
    valid_search_types = ["general", "pricing", "metrics", "chart"]
    if search_type.lower() not in valid_search_types:
        logger.warning(f"Invalid search_type '{search_type}' for stock agent, defaulting to 'general'")
        search_type = "general"

    client = _session_manager.get_client("stock")
    if client is None:
        error_msg = "Error: Stock data service is currently unavailable. Please try again later."
        logger.error("Stock client session not available in session manager")
        return error_msg

    try:
        stock_tools = client.list_tools_sync()
        if not stock_tools:
            error_msg = "Error: Stock analysis tools are currently unavailable. Please contact support if this persists."
            logger.error("Stock client session has no available tools")
            return error_msg

        logger.info(f"Stock analysis initiated - Query: '{sanitized_query[:50]}...', Type: {search_type}, Tools: {len(stock_tools)}")

        model = get_model()
        if not model:
            error_msg = "Error: Stock analysis model configuration unavailable. Please try again."
            logger.error("Failed to get model configuration for stock agent")
            return error_msg

        stock_analysis_agent = Agent(
            name="stock_analysis_agent",
            model=model, 
            system_prompt=prompt.stock_system_prompt, 
            tools=stock_tools
        )
        
        logger.info(f"Executing stock analysis for: '{sanitized_query}'")

        response = stock_analysis_agent(sanitized_query)
        
        if not response:
            return "Error: Stock analysis completed but no results were returned. Please verify the stock ticker symbol and try again."
        
        # Check if there's a stored chart to display by looking for recent chart files
        try:
            response_str = str(response)
            # Check if the response mentions chart creation
            if any(keyword in response_str.lower() for keyword in ["chart", "performance", "return", "graph", "plot", "visualization"]):
                charts_dir = "outputs/charts"
                if os.path.exists(charts_dir):
                    chart_files = [f for f in os.listdir(charts_dir) if f.endswith('.png')]
                    if chart_files:
                        chart_files.sort(key=lambda x: os.path.getmtime(os.path.join(charts_dir, x)), reverse=True)
                        latest_chart = chart_files[0]
                        chart_filepath = os.path.join(charts_dir, latest_chart)
                        
                        global chart_image_path
                        chart_image_path = chart_filepath
                        
                        chart_info = f"\n\n📊 **Chart Generated**: {latest_chart}\n*Chart will be displayed below the response.*"
                        response = response_str + chart_info
                        
                        logger.info(f"Chart stored for display: {chart_filepath}")
                
        except Exception as e:
            logger.warning(f"Could not retrieve stored chart: {e}")
        
        logger.info(f"Stock analysis completed successfully for: '{sanitized_query[:50]}...'")
        
        return str(response)

    except Exception as e:
        error_msg = f"Error in stock analysis: {str(e)}"
        logger.error(f"Stock agent error - Query: '{sanitized_query}', Error: {error_msg}")
        
        return (
            "Error: An issue occurred during stock analysis. This could be due to "
            "invalid ticker symbol, service availability, or data complexity. "
            "Please verify your stock symbol and try again, or contact support if the issue persists."
        )

# ============================================================================
# A specialized agent for searching market outlook using tavily MCP
# ============================================================================
@tool
def market_search_agent(query: str, search_type: str = "news") -> str:
    """
    Specialized market research agent for comprehensive economic and financial market analysis.
    
    This agent focuses specifically on market trends, economic indicators, and financial sector analysis,
    providing targeted intelligence for investment decision-making and market positioning strategies.

    Args:
        query (str): Market-focused search query or economic question. Should be specific to:
            - Economic indicators and trends
            - Market sector analysis
            - Financial instrument performance
            - Regulatory and policy impacts
            - Industry-specific developments
        search_type (str): Type of market search to perform. Options:
            - "news": Recent market news and current financial events (default)
            - "general": Comprehensive market analysis across multiple sources
            - "answer": Direct answer-focused search for specific market questions

    Returns:
        str: Structured market intelligence response containing:
            - Current market conditions and trend analysis
            - Economic indicators and their implications
            - Sector-specific insights and performance data
            - Regulatory considerations and policy impacts
            - Source citations with publication dates and hyperlinks
            - Risk assessments and market outlook considerations
            - Professional disclaimers and analytical limitations

    Raises:
        Returns error message string if client unavailable or search fails
    """
    # Input validation with market-specific context
    if not query or not query.strip():
        return "Error: Market research query cannot be empty. Please provide a specific market or economic question."
    
    valid_search_types = ["general", "news", "answer"]
    if search_type.lower() not in valid_search_types:
        logger.warning(f"Invalid search_type '{search_type}' for market search, defaulting to 'news'")
        search_type = "news"
    
    # Get Tavily client session
    client = _session_manager.get_client("tavily")
    if client is None:
        error_msg = "Error: Market research service is currently unavailable. Please try again later."
        logger.error("Tavily client session not available for market search")
        return error_msg

    try:
        # Validate client session and available tools
        tavily_tools = client.list_tools_sync()
        if not tavily_tools:
            error_msg = "Error: Market research tools are currently unavailable. Please contact support if this persists."
            logger.error("Tavily client session has no available tools for market search")
            return error_msg

        logger.info(f"Market research initiated - Query: '{query[:50]}...', Type: {search_type}, Tools: {len(tavily_tools)}")

        model = get_model()
        if not model:
            error_msg = "Error: Market research model configuration unavailable. Please try again."
            logger.error("Failed to get model configuration for market search agent")
            return error_msg

        market_agent = Agent(
            name="market_search_agent",
            model=model, 
            system_prompt=prompt.market_search_prompt, 
            tools=tavily_tools
        )

        # Enhance query with market-specific context for better results
        enhanced_query = _enhance_market_query(query, search_type)
        
        logger.info(f"Executing market research with enhanced query: '{enhanced_query[:100]}...'")

        response = market_agent(enhanced_query)
        
        if not response:
            return "Error: Market research completed but no results were returned. Please try rephrasing your query with more specific market terms."
        
        logger.info(f"Market research completed successfully for query: '{query[:50]}...'")
        
        return str(response)

    except Exception as e:
        error_msg = f"Error during market research execution: {str(e)}"
        logger.error(f"Market search agent error - Query: '{query}', Error: {error_msg}")
        
        return (
            "Error: An issue occurred while conducting market research. This could be due to "
            "network connectivity, service availability, or query complexity. "
            "Please try again with a more specific market-focused query or contact support if the issue persists."
        )

def _enhance_market_query(query: str, search_type: str) -> str:
    """
    Enhance market research query with financial and economic context for optimal results.
    
    Args:
        query: Original market research query
        search_type: Type of search being performed
        
    Returns:
        Enhanced query string optimized for market and economic research
    """
    query = query.strip()
    
    # Apply market-specific enhancements based on search type
    if search_type.lower() == "news":
        enhanced_query = f"LATEST MARKET NEWS AND FINANCIAL DEVELOPMENTS: {query}"
        if not any(term in query.lower() for term in ["recent", "latest", "current", "today"]):
            enhanced_query += " (focus on recent market movements, earnings, and economic announcements)"
            
    elif search_type.lower() == "answer":
        enhanced_query = f"MARKET ANALYSIS AND FINANCIAL ANSWER: {query}"
        if "?" not in query:
            enhanced_query += " - provide specific market data, financial metrics, and analytical insights with sources"
            
    else:  # general market search
        enhanced_query = f"COMPREHENSIVE MARKET AND ECONOMIC RESEARCH: {query}"
        enhanced_query += " (provide detailed market analysis, economic indicators, sector trends, and multiple expert perspectives)"
    
    # Add market-specific context keywords for better targeting
    market_keywords = [
        "financial markets", "economic indicators", "investment analysis", 
        "market trends", "sector performance", "regulatory impact"
    ]
    
    # If query doesn't contain market-specific terms, add context
    if not any(keyword.split()[0] in query.lower() for keyword in market_keywords):
        enhanced_query += f" - include relevant market context and economic implications"
    
    return enhanced_query

# ============================================================================
# A specialized agent for generating PDF report
# ============================================================================
@tool
def generate_pdf_report(report_content: str, filename: str) -> str:
    """
    Specialized agent for creating PDF report

    Args:
        report_content
        filename

    Returns:
        Provide report name and location
    """
    try:
        # Ensure directory exists
        os.makedirs("outputs/reports", exist_ok=True)

        # Add timestamp to filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_filename = f"{filename}_{timestamp}"

        # Set up the PDF file
        filepath = f"outputs/reports/{timestamped_filename}.pdf"
        doc = SimpleDocTemplate(filepath, pagesize=letter)

        font_path = "assets/AmazonEmber_Lt.ttf"
        pdfmetrics.registerFont(TTFont("AmazonEmber", font_path))

        # Create styles
        styles = getSampleStyleSheet()
        styles.add(
            ParagraphStyle(name="Normal_KO", fontName="AmazonEmber", fontSize=10)
        )
        styles.add(
            ParagraphStyle(name="Heading1_KO", fontName="AmazonEmber", fontSize=16)
        )

        def detect_table(lines, start_idx):
            """Detect if lines form a table starting at start_idx"""
            if start_idx >= len(lines):
                return None, start_idx
            
            table_lines = []
            i = start_idx
            
            # Look for table patterns (lines with | separators)
            while i < len(lines):
                line = lines[i].strip()
                if '|' in line and line.count('|') >= 2:
                    table_lines.append(line)
                    i += 1
                elif line.startswith('|') and line.endswith('|'):
                    table_lines.append(line)
                    i += 1
                elif not line:  # Empty line might separate table sections
                    i += 1
                    continue
                else:
                    break
            
            if len(table_lines) >= 2:  # At least header + one row
                return table_lines, i
            return None, start_idx

        def parse_table(table_lines):
            """Parse table lines into a 2D array"""
            table_data = []
            for line in table_lines:
                # Skip separator lines (lines with only |, -, and spaces)
                if re.match(r'^[|\s-]+$', line):
                    continue
                
                # Split by | and clean up
                cells = [cell.strip() for cell in line.split('|')]
                # Remove empty cells at start/end
                if cells and not cells[0]:
                    cells = cells[1:]
                if cells and not cells[-1]:
                    cells = cells[:-1]
                
                if cells:  # Only add non-empty rows
                    table_data.append(cells)
            
            return table_data

        # Process content
        elements = []
        lines = report_content.split("\n")
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for table
            table_lines, next_i = detect_table(lines, i)
            if table_lines:
                table_data = parse_table(table_lines)
                if table_data:
                    # Create table
                    table = Table(table_data)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'AmazonEmber'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('FONTNAME', (0, 1), (-1, -1), 'AmazonEmber'),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(table)
                    elements.append(Spacer(1, 12))
                i = next_i
                continue
            
            # Process regular content
            if line.startswith("# "):
                elements.append(Paragraph(line[2:], styles["Heading1_KO"]))
                elements.append(Spacer(1, 12))
            elif line.startswith("## "):
                elements.append(Paragraph(line[3:], styles["Heading2"]))
                elements.append(Spacer(1, 10))
            elif line.startswith("### "):
                elements.append(Paragraph(line[4:], styles["Heading3"]))
                elements.append(Spacer(1, 8))
            elif line.strip():  # Skip empty lines
                elements.append(Paragraph(line, styles["Normal_KO"]))
                elements.append(Spacer(1, 6))
            
            i += 1

        # Build PDF
        doc.build(elements)

        return f"PDF report generated successfully: {filepath}"
    except Exception as e:
        error_msg = f"Error generating PDF: {e}"
        logger.error(error_msg)
        return f"Error: Failed to generate PDF report. {str(e)}"

# ============================================================================
# MCP Client Session Distribution Mechanism
# ============================================================================
class MCPClientSessionManager:
    """Manages and distributes MCP client sessions to specialized agent tools"""

    def __init__(self):
        self._active_clients = {}
        self._session_status = {}

    def set_active_clients(self, client_sessions: dict):
        """
        Set the active MCP client sessions for distribution to agent tools

        Args:
            client_sessions: Dictionary mapping client types to active MCP client instances
        """
        self._active_clients = client_sessions.copy()
        # Track session status for each client
        for client_type, client in client_sessions.items():
            self._session_status[client_type] = {
                "active": True,
                "client": client,
                "last_used": None,
            }
        logger.info(
            f"Active MCP client sessions set: {list(self._active_clients.keys())}"
        )

    def get_client(self, client_type: str):
        """
        Get an active MCP client session by type

        Args:
            client_type: Type of client ('tavily', 'kb', 'database', 'stock')

        Returns:
            Active MCP client instance or None if not available
        """
        if client_type in self._active_clients:
            client = self._active_clients[client_type]

            self._session_status[client_type]["last_used"] = datetime.now()
            return client
        return None

    def get_all_clients(self) -> dict:
        """Return dictionary of all active MCP client sessions"""
        return self._active_clients.copy()

    def is_client_available(self, client_type: str) -> bool:
        """Check if a specific client type is available and active"""
        return client_type in self._active_clients and self._session_status.get(
            client_type, {}
        ).get("active", False)

    def get_session_status(self) -> dict:
        """Get status information for all client sessions"""
        return self._session_status.copy()

# Global session manager instance
_session_manager = MCPClientSessionManager()

def get_chart_image_path():
    """Get the stored chart image path for Streamlit display"""
    global chart_image_path
    return chart_image_path

def clear_chart_image_path():
    """Clear the stored chart image path after display"""
    global chart_image_path
    chart_image_path = None

# ============================================================================
# Triage the query, sinple agent vs graph agent
# ============================================================================
def triage_query(question, history_mode, st):
    message_placeholder = st.empty()
    full_response = ""
    tool_usage_count = {}  # Track tool usage counts

    async def process_streaming_response():
        nonlocal full_response
        try:
            # Open all client sessions at once and manage them
            with tavily_mcp_client as tavily_client, kb_mcp_client as kb_client, athena_mcp_client as database_client, stock_mcp_client as stock_client:

                client_sessions = {
                    "tavily": tavily_client,
                    "kb": kb_client,
                    "database": database_client,
                    "stock": stock_client,
                }

                # Distribute active client sessions to specialized agent tools
                _session_manager.set_active_clients(client_sessions)

                session_status = _session_manager.get_session_status()
                logger.info(
                    f"MCP client session distribution status: {list(session_status.keys())}"
                )

                # Triage agent to determine routing
                triage_agent = Agent(name="triage_agent", system_prompt=prompt.triage_agent_prompt, model=get_model())
                triage_response = triage_agent(question)

                try:
                    response_text = str(triage_response)
                    if response_text == "graph":
                        agent = create_graph_agent()
                    else:
                        agent = create_qna_agent()
                except Exception as e:
                    logger.error(f"Error parsing triage response: {e}")
                    agent = create_qna_agent()

                # Stream the response in real-time with timeout protection
                try:
                    async with asyncio.timeout(1200):  # 20 minute timeout for long operations
                        async for item in agent.stream_async(question):
                            if "message" in item and "content" in item["message"] and "role" in item["message"] and item["message"]["role"] == "assistant":
                                for content_item in item['message']['content']:
                                    if "toolUse" in content_item:
                                        tool_name = content_item["toolUse"].get('name', 'unknown')
                                        tool_id = content_item["toolUse"].get('toolUseId', '')
                                        tool_input = content_item["toolUse"].get('input', {})
                                        
                                        if tool_name not in tool_usage_count:
                                            tool_usage_count[tool_name] = 0
                                        tool_usage_count[tool_name] += 1
                                        
                                        if full_response and not full_response.endswith('\n\n'):
                                            full_response += '\n\n'

                                        count_suffix = f" (#{tool_usage_count[tool_name]})" if tool_usage_count[tool_name] > 1 else ""
                                        
                                        if tool_name == 'execute_sql_query' and 'description' in tool_input:
                                            tool_info = f"🔍 {tool_input['description']}{count_suffix}\n\n"
                                        elif tool_name == 'get_tables_information':
                                            tool_info = f"⚙️ Retrieving table information{count_suffix}...\n\n"
                                        elif tool_name == 'current_time':
                                            tool_info = f"⚙️ Getting current time{count_suffix}...\n\n"
                                        elif tool_name == 'client_meeting_analysis':
                                            tool_info = f"📋 Analyzing client meeting{count_suffix}...\n\n"
                                        elif tool_name == 'web_search_agent':
                                            query_preview = str(tool_input.get('query', ''))[:50]
                                            tool_info = f"🌐 Searching web{count_suffix}: {query_preview}...\n\n"
                                        elif tool_name == 'market_search_agent':
                                            query_preview = str(tool_input.get('query', ''))[:50]
                                            tool_info = f"📈 Researching market{count_suffix}: {query_preview}...\n\n"
                                        elif tool_name == 'database_query_agent':
                                            query_preview = str(tool_input.get('query', ''))[:50]
                                            tool_info = f"⚙️ Querying database{count_suffix}: {query_preview}...\n\n"
                                        elif tool_name == 'stock_agent':
                                            query_preview = str(tool_input.get('query', ''))[:50]
                                            tool_info = f"📊 Fetching stock data{count_suffix}: {query_preview}...\n\n"
                                        elif tool_name == 'knowledge_bases_agent':
                                            tool_info = f"📚 Searching knowledge bases{count_suffix}...\n\n"
                                        elif tool_name == 'generate_pdf_report':
                                            tool_info = f"📄 Generating PDF report{count_suffix}...\n\n"
                                        else:
                                            # Generic tool use notification for all other tools
                                            tool_info = f"🛠️ Using tool: {tool_name}{count_suffix}\n\n"
                                        
                                        full_response += tool_info
                                        message_placeholder.markdown(full_response, unsafe_allow_html=True)
                                        logger.info(f"Tool used: {tool_name}{count_suffix} (ID: {tool_id[:8]}...)")
                            
                            # Handle tool results
                            elif "message" in item and "content" in item["message"] and "role" in item["message"] and item["message"]["role"] == "user":
                                for content_item in item['message']['content']:
                                    if "toolResult" in content_item:
                                        tool_result = content_item["toolResult"]
                                        tool_id = tool_result.get('toolUseId', '')
                                        status = tool_result.get('status', 'unknown')
                                        
                                        if status == "success":
                                            logger.info(f"✅ Tool completed successfully (ID: {tool_id[:8]}...)")
                                        else:
                                            logger.warning(f"❌ Tool failed (ID: {tool_id[:8]}...)")
                            
                            # Handle streaming data chunks
                            elif "data" in item:
                                full_response += item['data']
                                message_placeholder.markdown(full_response, unsafe_allow_html=True)
                except asyncio.TimeoutError:
                    logger.error("Streaming response timed out after 10 minutes")
                    full_response += "\n\n⚠️ Response generation timed out. Please try again with a simpler query."
                    message_placeholder.markdown(full_response, unsafe_allow_html=True)

                logger.info(f"Final response: {repr(full_response)}")
                logger.info(f"Tool usage summary: {tool_usage_count}")

        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            message_placeholder.markdown(
                "Sorry, an error occurred while generating the response."
            )
            logger.error(traceback.format_exc()) 
    
    # Handle event loop properly to avoid conflicts with existing loops (e.g., Streamlit)
    try:
        
        loop = asyncio.get_running_loop()
        nest_asyncio.apply()
        loop.run_until_complete(process_streaming_response())
    except RuntimeError:
        asyncio.run(process_streaming_response())
    
    return full_response

# ============================================================================
# Q&A agent that utilizes 1-3 sub-agents
# ============================================================================
def create_qna_agent(system_prompt: str = None) -> Agent:
    """
    Creates a comprehensive financial advisor agent with specialized tools and capabilities.
    
    This agent serves as the primary interface for financial advisory services, equipped with
    multiple specialized tools to handle diverse client needs and data sources.

    Available Tools & Capabilities:
    
    ## Tool Usage Guidelines:
    - For client meeting analysis: Use `client_meeting_analysis` to retrieve information from knowledge base
    - For web research: Use `web_search_agent` for general financial information or `market_search_agent` for market-specific data
    - For portfolio data: Use `database_query_agent` to access client portfolio and performance information
    - For stock information: Use `stock_agent` for real-time pricing and historical data
    - For report creation: Use `generate_pdf_report` to create professional client reports
    - For file operations: Use appropriate file reading tools for document analysis

    Response Formatting Standards:
    
    📈 Portfolio Data:
        • Portfolio overviews: Bullet point summaries with key metrics
        • Holdings & securities: Structured table format with allocations
        • Performance vs benchmarks: Comparative table with returns and ratios
        • Security holdings: Detailed table with positions and valuations
    
    🌐 Research Data:
        • Web search results: Include source hyperlinks and publication dates
        • Market analysis: Structured insights with data attribution
        • Stock information: Real-time pricing with market context
    
    📋 Meeting Analysis:
        • Sentiment assessment with supporting evidence
        • Key decisions and action items highlighted
        • Negative feedback: <span style="color:red; font-weight:bold">highlighted in red</span>
        • Positive feedback: <span style="color:blue; font-weight:bold">highlighted in blue</span>

    Returns:
        Agent: Configured financial advisor agent with all specialized tools and formatting capabilities
    """
    return Agent(
        model=get_model(),
        system_prompt=prompt.qna_agent_prompt,
        tools=[client_meeting_analysis, knowledge_bases_agent, database_query_agent, generate_pdf_report, web_search_agent, market_search_agent, stock_agent]
    )

# ============================================================================
# Graph agent that utilizes 5+ agents
# ============================================================================
def create_graph_agent(system_prompt: str = None):
    """
    This function performs the following tasks:
    Customer Meeting Summary:
        - Generate a summary of the customer meeting.
        - Identify specific action items discussed during the meeting.
     Action Item Research:
        - For each identified action item, conduct a web search to find relevant and up-to-date information.
        - Include hyperlinks to the data sources in the response to ensure transparency and verifiability.
        - Present the findings in a clear and concise manner.
    Customer Portfolios Overview:
        - Provide an overview of the customer's portfolios.
        - Detail the holdings within each portfolio.
    Portfolio Holdings Analysis:
        - For each holding, perform a web search to identify key recent trends and news.
        - Include hyperlinks to the data sources in the response to ensure transparency and verifiability.
    Market Analysis:
        - Recent stock market trends and key economic events

    Args:
    system_prompt (str, optional): A custom system prompt to guide the agent. Defaults to None.

    Returns:
    Information containing the meeting summary, action items, relevant answers, and portfolio and investment infomration with hyperlinks to data sources.
    If the response includes a portfolio overview, it will be summarized in bullet point format.
    If the response includes portfolio holdings and securities data, it will be displayed in a table format.
    If the response includes portfolio performance data against benchmark, they will be displayed in a table format.
    If the response includes Security Holdings, they will be displayed in a table format.
    For web search data, ensure to include hyperlink of the source. 
    """
    logger.info(f"\n###### Start Graph Agent Process #####\n")
    
    # Get database prompt with schema
    db_prompt = prompt.get_database_query_prompt()
        
    client_meeting_coordinator_agent = Agent(name="graph_meeting_coordinator", model=get_model(), system_prompt=prompt.coordinator_prompt)
    client_meeting_analysis_agent = Agent(name="graph_meeting_analyzer", model=get_model(),system_prompt=prompt.customer_meeting_analysis_agent_prompt, tools=[client_meeting_analysis])
    client_action_item_analysis_agent = Agent(name="graph_action_item_analyzer", model=get_model(),system_prompt=prompt.customer_meeting_action_item_prompt, tools=[client_meeting_analysis])
    graph_web_search_agent = Agent(name="graph_web_researcher", model=get_model(), system_prompt=prompt.web_search_prompt, tools=[web_search_agent])
    graph_database_query_agent = Agent(name="graph_database_analyst", model=get_model(), system_prompt=db_prompt, tools=[database_query_agent])
    graph_market_search_agent = Agent(name="graph_market_researcher", model=get_model(), system_prompt=prompt.market_search_prompt, tools=[market_search_agent])
    synthesis_agent = Agent(name="graph_synthesizer", model=get_model(),system_prompt=prompt.synthesis_prompt)
    report_writer_agent = Agent(name="graph_report_writer", model=get_model(),system_prompt="Create a report using generate_pdf_report tool", tools=[generate_pdf_report])

    try:
        # Build the graph
        builder = GraphBuilder()

        # Add the nodes
        builder.add_node(client_meeting_coordinator_agent, "client_meeting_coordinator_agent")
        builder.add_node(client_meeting_analysis_agent, "client_meeting_analysis_agent")
        builder.add_node(client_action_item_analysis_agent, "client_action_item_analysis_agent")
        builder.add_node(graph_web_search_agent, "graph_web_search_agent")
        builder.add_node(graph_database_query_agent, "graph_database_query_agent")
        builder.add_node(graph_market_search_agent, "graph_market_search_agent")
        builder.add_node(synthesis_agent, "synthesis_agent")
        builder.add_node(report_writer_agent, "report_writer_agent")

        # Add the edges
        builder.add_edge("client_meeting_coordinator_agent", "client_meeting_analysis_agent")
        builder.add_edge("client_meeting_analysis_agent", "client_action_item_analysis_agent")
        builder.add_edge("client_action_item_analysis_agent", "graph_web_search_agent")
        builder.add_edge("graph_web_search_agent", "synthesis_agent")
        builder.add_edge("client_meeting_coordinator_agent", "graph_database_query_agent")
        builder.add_edge("graph_database_query_agent", "synthesis_agent")
        builder.add_edge("client_meeting_coordinator_agent", "graph_market_search_agent")
        builder.add_edge("graph_market_search_agent", "synthesis_agent")
        builder.add_edge("synthesis_agent", "report_writer_agent")

        builder.set_entry_point("client_meeting_coordinator_agent")
        return builder.build()
        
    except Exception as e:
        logger.error(f"Error creating graph agent: {e}")
        logger.warning("Falling back to QnA agent due to graph creation failure")
        return create_qna_agent()