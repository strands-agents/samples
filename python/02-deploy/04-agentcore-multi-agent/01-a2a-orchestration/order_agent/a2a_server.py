"""Order Agent deployed to Amazon Bedrock AgentCore with A2A protocol support.

Queries customer orders from Amazon DynamoDB using the awslabs.dynamodb-mcp-server
MCP tool. Uses async lifespan pattern for MCP subprocess initialization to ensure
health checks pass before tool loading begins.

Key concepts demonstrated:
- A2A protocol server for multi-agent orchestration (port 9000)
- MCP client with stdio transport for DynamoDB access
- Two-phase initialization: fast startup, then async tool loading
- Graceful degradation if MCP subprocess fails
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

import boto3
import uvicorn
from fastapi import FastAPI
from mcp import StdioServerParameters, stdio_client
from strands import Agent
from strands.models import BedrockModel
from strands.multiagent.a2a import A2AServer
from strands.telemetry import StrandsTelemetry
from strands.tools.mcp import MCPClient

# --- Logging ---

logging.basicConfig(level=logging.INFO)
logging.getLogger("strands").setLevel(logging.INFO)
logging.getLogger("a2a").setLevel(logging.DEBUG)
logging.getLogger("strands.multiagent.a2a").setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

# Enable distributed tracing with AWS X-Ray
StrandsTelemetry().setup_otlp_exporter()

# --- Configuration ---

PORT = 9000  # A2A protocol uses port 9000 (HTTP protocol uses 8080)
SSM_ORDER_AGENT_URL = "/ecommerce-assistant/order-agent-url"
SSM_ORDERS_TABLE = "/ecommerce-assistant/orders-table"

# Timeouts prevent container hangs if MCP server fails to start
MCP_STARTUP_TIMEOUT = 10.0  # Max seconds to wait for subprocess
MCP_TOOLS_TIMEOUT = 5.0     # Max seconds to fetch tool definitions

SYSTEM_PROMPT_TEMPLATE = """You are an Order Agent for an e-commerce shopping assistant.

Query the "{table_name}" DynamoDB table for order information.
Return order details including product_ids so the Orchestrator can fetch product details."""


# --- Callback Handler ---


class ToolLoggingHandler:
    """Log tool invocations to CloudWatch for debugging multi-agent workflows.
    
    Tracks which tools the agent calls and with what inputs. Useful for:
    - Debugging why an agent gave a certain response
    - Monitoring A2A calls in distributed systems
    - Building observability dashboards
    """

    def __init__(self) -> None:
        self.logged_tool_ids: set[str] = set()  # Prevent duplicate logs
        self.tool_count = 0

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


# --- Helper Functions ---


def get_table_name() -> str:
    """Get DynamoDB table name from environment variable or SSM Parameter Store.
    
    Checks ORDERS_TABLE env var first (useful for local dev), then falls back
    to SSM (standard for AgentCore deployments where secrets are stored in SSM).
    """
    if table_name := os.environ.get("ORDERS_TABLE"):
        logger.info(f"Using table from env: {table_name}")
        return table_name

    try:
        ssm = boto3.client("ssm")
        response = ssm.get_parameter(Name=SSM_ORDERS_TABLE, WithDecryption=True)
        table_name = response["Parameter"]["Value"]
        logger.info(f"Using table from SSM: {table_name}")
        return table_name
    except Exception as e:
        logger.error(f"Could not get table name: {e}")
        raise


def get_runtime_url() -> str | None:
    """Get AgentCore runtime URL for agent card generation.
    
    The runtime URL is needed for the A2A agent card (/.well-known/agent-card.json)
    so other agents can discover and call this agent. Without it, the agent card
    will have an internal URL that won't work for external A2A calls.
    """
    if url := os.environ.get("ORDER_AGENT_URL"):
        logger.info(f"Using runtime URL from env: {url}")
        return url

    try:
        ssm = boto3.client("ssm")
        response = ssm.get_parameter(Name=SSM_ORDER_AGENT_URL, WithDecryption=True)
        url = response["Parameter"]["Value"]
        logger.info(f"Using runtime URL from SSM: {url}")
        return url
    except Exception as e:
        logger.warning(f"Could not get runtime URL: {e}")
        return None


# --- Agent Creation ---
# Create agent with tools=[] for fast module import. MCP tools are added later
# in server_lifespan() after the server binds to port 9000.
#
# Why this pattern? AgentCore health checks need port 9000 responsive immediately.
# MCP subprocess startup can take several seconds, so we defer it to lifespan.

region = boto3.session.Session().region_name or "us-west-2"

order_agent = Agent(
    name="Ecommerce_Order_Agent",
    description="Looks up order information from DynamoDB for customers",
    system_prompt="Order agent initializing...",  # Updated in server_lifespan
    model=BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name=region,
    ),
    tools=[],  # Empty - MCP tools added in server_lifespan after startup
    callback_handler=ToolLoggingHandler(),
)
logger.info(f"Agent created: {order_agent.name}")

# MCP connection handle - initialized in server_lifespan, cleaned up on shutdown
mcp_tool_connection: MCPClient | None = None


# --- Server Lifespan (startup and shutdown) ---


@asynccontextmanager
async def server_lifespan(app: FastAPI):
    """Initialize MCP tools after server starts, clean up on shutdown.
    
    This runs AFTER uvicorn binds to port 9000, so health checks pass immediately.
    The MCP subprocess starts here, not during module import.
    
    Sequence:
    1. Module imports → agent created with tools=[] (fast, ~milliseconds)
    2. uvicorn binds to port 9000 → /ping endpoint ready
    3. AgentCore health checks pass → container marked healthy
    4. THIS FUNCTION runs → MCP subprocess starts → tools added to agent
    5. Agent ready to handle A2A requests with DynamoDB access
    """
    global mcp_tool_connection

    logger.info("=== Order Agent Startup ===")

    try:
        table_name = get_table_name()

        # Launch DynamoDB MCP server as subprocess via uvx (auto-installs package)
        # The MCP server provides query/scan tools that the agent uses to read orders
        mcp_tool_connection = MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command="uvx",
                    args=["awslabs.dynamodb-mcp-server@latest"],
                    env={
                        **os.environ,  # Inherit AWS credentials from container's IAM role
                        "AWS_REGION": region,
                        "DDB_TABLE_NAME": table_name,
                    },
                )
            )
        )

        # Start the MCP subprocess with timeout protection
        # Why run_in_executor? The __enter__ call blocks synchronously, which would
        # freeze the event loop. Running in executor keeps health checks responsive.
        event_loop = asyncio.get_event_loop()
        start_mcp_subprocess = mcp_tool_connection.__enter__
        await asyncio.wait_for(
            event_loop.run_in_executor(None, start_mcp_subprocess),
            timeout=MCP_STARTUP_TIMEOUT,
        )
        logger.info("MCP tool connection started")

        # Fetch available tools from MCP server (e.g., query_table, scan_table)
        mcp_tools = await asyncio.wait_for(
            event_loop.run_in_executor(None, mcp_tool_connection.list_tools_sync),
            timeout=MCP_TOOLS_TIMEOUT,
        )
        logger.info(f"Loaded {len(mcp_tools)} tools from MCP server")

        # Attach tools to agent - works because A2AServer holds a reference (not copy)
        # to the agent object, so modifying order_agent.tools here affects request handling
        order_agent.tools = mcp_tools
        order_agent.system_prompt = SYSTEM_PROMPT_TEMPLATE.format(table_name=table_name)

        logger.info(f"=== Startup Complete: {order_agent.name} with {len(mcp_tools)} tools ===")

    except asyncio.TimeoutError:
        # Graceful degradation: agent stays healthy but can't query DynamoDB
        logger.error("MCP initialization timed out - agent will operate without tools")
    except Exception as e:
        logger.error(f"Startup error: {e} - agent will operate without tools")

    yield  # Server is running, handling A2A requests

    # Shutdown: clean up MCP subprocess
    logger.info("=== Shutting Down ===")
    if mcp_tool_connection:
        try:
            stop_mcp_subprocess = mcp_tool_connection.__exit__
            stop_mcp_subprocess(None, None, None)
            logger.info("MCP tool connection closed")
        except Exception as e:
            logger.error(f"Error closing MCP: {e}")


# --- FastAPI App and A2A Server ---

runtime_url = get_runtime_url()

a2a_server = A2AServer(
    agent=order_agent,
    host="0.0.0.0",  # Listen on all interfaces (required for container networking)
    port=PORT,
    http_url=runtime_url,  # Used in agent card for A2A discovery
    serve_at_root=True,    # Serve agent card at /.well-known/agent-card.json
)

app = FastAPI(title="Order Agent A2A Server", lifespan=server_lifespan)


@app.get("/ping")
def ping():
    """Health check endpoint for AgentCore container probes."""
    return {"status": "healthy"}


app.mount("/", a2a_server.to_fastapi_app())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
