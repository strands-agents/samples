"""Product Agent deployed to Amazon Bedrock AgentCore with A2A protocol support.

Queries product catalog from DummyJSON API (https://dummyjson.com) using custom
tools built with the Strands @tool decorator.

Key features:
- A2A protocol server for multi-agent orchestration via Agent-to-Agent messaging
- Custom HTTP request tools for external API access
- OpenTelemetry instrumentation for AWS X-Ray distributed tracing
"""

import json
import logging
import os
from typing import Any

import boto3
import requests
import uvicorn
from fastapi import FastAPI
from strands import Agent, tool
from strands.models import BedrockModel
from strands.multiagent.a2a import A2AServer
from strands.telemetry import StrandsTelemetry

# =============================================================================
# Logging Configuration
# =============================================================================

logging.basicConfig(level=logging.INFO)
logging.getLogger("strands").setLevel(logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenTelemetry exporter for AWS X-Ray distributed tracing
StrandsTelemetry().setup_otlp_exporter()

# =============================================================================
# Configuration
# =============================================================================

PORT = 9000  # A2A protocol requires port 9000 (HTTP protocol uses 8080)
SSM_PRODUCT_AGENT_URL = "/ecommerce-assistant/product-agent-url"

SYSTEM_PROMPT = """You are a Product Agent for an e-commerce assistant.

You have access to tools that query a product catalog with 194+ products across multiple categories.

Available tools:
- search_products: Search for products by keyword (e.g., "laptop", "phone")
- get_products_by_category: Get products from specific categories
- get_all_products: Browse all available products

Electronics categories available:
- laptops (MacBook Pro, Dell XPS, ThinkPad, etc.)
- smartphones (iPhone, Samsung, Google Pixel, etc.)
- tablets (iPad, Samsung Tab, etc.)
- mobile-accessories (phone cases, chargers, etc.)

Other categories: beauty, fragrances, furniture, groceries, mens-shirts, womens-dresses, and more.

Help customers find products by searching, browsing categories, or filtering by price.
If a product isn't found, suggest similar alternatives from available categories.
"""

# =============================================================================
# Product Catalog Tools
# =============================================================================


@tool
def search_products(query: str, limit: int = 10) -> str:
    """Search for products by keyword across all categories.

    Args:
        query: Search term (e.g., "laptop", "phone", "MacBook")
        limit: Maximum number of products to return (default: 10)

    Returns:
        JSON string with matching products including id, title, price, category, description
    """
    try:
        response = requests.get(
            "https://dummyjson.com/products/search",
            params={"q": query, "limit": limit},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        # Simplify response to essential fields
        products = [
            {
                "id": p["id"],
                "title": p["title"],
                "price": p["price"],
                "category": p["category"],
                "description": p["description"],
                "rating": p.get("rating", "N/A"),
                "stock": p.get("stock", "N/A"),
            }
            for p in data.get("products", [])
        ]

        return json.dumps(
            {"products": products, "total": data.get("total", 0)}, indent=2
        )
    except Exception as e:
        return json.dumps({"error": f"Failed to search products: {str(e)}"})


@tool
def get_products_by_category(category: str, limit: int = 10) -> str:
    """Get products from a specific category.

    Args:
        category: Category name (e.g., "laptops", "smartphones", "tablets", "beauty")
        limit: Maximum number of products to return (default: 10)

    Returns:
        JSON string with products from the specified category
    """
    try:
        response = requests.get(
            f"https://dummyjson.com/products/category/{category}",
            params={"limit": limit},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        # Simplify response to essential fields
        products = [
            {
                "id": p["id"],
                "title": p["title"],
                "price": p["price"],
                "category": p["category"],
                "description": p["description"],
                "rating": p.get("rating", "N/A"),
                "stock": p.get("stock", "N/A"),
            }
            for p in data.get("products", [])
        ]

        return json.dumps(
            {"products": products, "total": data.get("total", 0), "category": category},
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {"error": f"Failed to get products from category '{category}': {str(e)}"}
        )


@tool
def get_all_products(limit: int = 10) -> str:
    """Get all available products across all categories.

    Args:
        limit: Maximum number of products to return (default: 10)

    Returns:
        JSON string with products from all categories
    """
    try:
        response = requests.get(
            "https://dummyjson.com/products",
            params={"limit": limit},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        # Simplify response to essential fields
        products = [
            {
                "id": p["id"],
                "title": p["title"],
                "price": p["price"],
                "category": p["category"],
                "description": p["description"],
                "rating": p.get("rating", "N/A"),
                "stock": p.get("stock", "N/A"),
            }
            for p in data.get("products", [])
        ]

        return json.dumps(
            {"products": products, "total": data.get("total", 0)}, indent=2
        )
    except Exception as e:
        return json.dumps({"error": f"Failed to get all products: {str(e)}"})


# =============================================================================
# Callback Handler
# =============================================================================


class ToolLoggingHandler:
    """Log tool execution events to Amazon CloudWatch Logs for debugging.

    Callback handler that receives agent lifecycle events during the reasoning loop.
    Invoked with **kwargs containing message dictionaries, tool invocations, and
    completion signals from the Strands agent execution engine.

    De-duplication strategy:
    Tool invocations may appear multiple times in the event stream when conversation
    history is replayed for context. Tracking toolUseId values ensures each tool
    execution is logged exactly once, maintaining a clear audit trail in CloudWatch.

    Use this pattern to:
    - Debug product search and API integration issues
    - Track external service calls (DummyJSON API) in multi-agent workflows
    - Build custom observability dashboards on Amazon Bedrock AgentCore metrics
    """

    def __init__(self) -> None:
        self.logged_tool_ids: set[str] = set()  # Deduplicate tool logs
        self.tool_count = 0  # Sequential counter for log readability

    def __call__(self, **kwargs: Any) -> None:
        message = kwargs.get("message", {})
        if isinstance(message, dict) and message.get("role") == "assistant":
            for content in message.get("content", []):
                if isinstance(content, dict):
                    tool_use = content.get("toolUse")
                    if tool_use:
                        tool_id = tool_use.get("toolUseId")
                        if tool_id and tool_id not in self.logged_tool_ids:
                            self.logged_tool_ids.add(tool_id)
                            self.tool_count += 1
                            tool_name = tool_use.get("name", "Unknown")
                            tool_input = tool_use.get("input", {})
                            logger.info(f"=== TOOL #{self.tool_count}: {tool_name} ===")
                            logger.info(f"TOOL INPUT: {json.dumps(tool_input)}")

        if kwargs.get("complete") and kwargs.get("data"):
            logger.info(f"=== COMPLETE: {len(kwargs.get('data', ''))} chars ===")


# =============================================================================
# Helper Functions
# =============================================================================


def get_runtime_url() -> str | None:
    """Retrieve Amazon Bedrock AgentCore runtime invocation URL.

    The runtime URL is the HTTPS endpoint that Amazon Bedrock AgentCore provides
    for this agent runtime. Required for:

    1. Agent card generation: A2AServer uses this URL in /.well-known/agent-card.json
       to advertise how other agents can reach this agent via A2A protocol.

    2. Multi-agent orchestration: Orchestrator uses this URL with a2a_send_message
       tool to route requests. Incorrect URL causes 404 errors during A2A calls.

    URL format:
    https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{escaped_arn}/invocations

    Stored in AWS Systems Manager Parameter Store after deployment and must match
    the actual AgentCore runtime endpoint for this agent.

    Returns:
        AgentCore HTTPS invocation endpoint, or None if not configured (agent card
        will use internal URL, limiting A2A discovery by external agents).
    """
    if url := os.environ.get("PRODUCT_AGENT_URL"):
        logger.info(f"Using runtime URL from environment: {url}")
        return url

    try:
        ssm = boto3.client("ssm")
        response = ssm.get_parameter(Name=SSM_PRODUCT_AGENT_URL, WithDecryption=True)
        url = response["Parameter"]["Value"]
        logger.info(f"Using runtime URL from SSM: {url}")
        return url
    except Exception as e:
        logger.warning(f"Could not get runtime URL from SSM: {e}")
        logger.warning("Agent card will use internal URL - A2A messaging may not work")
        return None


# =============================================================================
# Agent and Server Setup
# =============================================================================

logger.info("=" * 60)
logger.info("=== Product Agent Server Starting ===")
logger.info("=" * 60)

region = boto3.session.Session().region_name or "us-west-2"

# Create agent with product catalog tools
logger.info("Creating agent with DummyJSON product catalog tools...")
agent = Agent(
    name="Ecommerce_Product_Agent",
    description="Fetches product information from DummyJSON catalog for browsing and discovery",
    system_prompt=SYSTEM_PROMPT,
    model=BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name=region,
    ),
    tools=[search_products, get_products_by_category, get_all_products],
    callback_handler=ToolLoggingHandler(),
)
logger.info(f"Agent created: {agent.name}")

# Retrieve runtime URL for A2A protocol agent card generation
runtime_url = get_runtime_url()

# Create A2AServer with container-ready networking configuration
a2a_server = A2AServer(
    agent=agent,
    host="0.0.0.0",
    port=PORT,  # 9000 for A2A protocol (HTTP protocol uses 8080)
    http_url=runtime_url,  # AgentCore runtime URL from SSM for agent card generation
    serve_at_root=True,  # Serve agent card at /.well-known/agent-card.json
)

# Create FastAPI application
app = FastAPI(title="Product Agent A2A Server")


@app.get("/ping")
def ping():
    """Health check endpoint for Amazon Bedrock AgentCore container probes.

    Returns:
        Status dictionary indicating agent health.
    """
    return {"status": "healthy"}


# Mount A2A server at root path
app.mount("/", a2a_server.to_fastapi_app())

logger.info("=" * 60)
logger.info("=== Product Agent Initialization Complete ===")
logger.info(f"A2A endpoints available at port {PORT}")
logger.info("=" * 60)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
