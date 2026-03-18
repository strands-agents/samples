"""Orchestrator Agent for e-commerce multi-agent orchestration.

Orchestrates Order Agent and Product Agent via A2A protocol to handle customer
queries about orders and products. Routes requests to appropriate specialist agents
and combines responses for unified customer experience.

Key features:
- A2AClientToolProvider for dynamic agent discovery via Agent Cards
- AWS Signature Version 4 (SigV4) authentication for Amazon Bedrock AgentCore
- Streaming callback handler for real-time progress updates
- Customer context propagation via tool_context for personalized queries
"""

import logging
from typing import Any

import boto3
from strands import Agent, tool
from strands.models import BedrockModel
from strands.types.tools import ToolContext
from strands_tools.a2a_client import A2AClientToolProvider

from sigv4_auth import SigV4HTTPXAuth

logging.getLogger().setLevel(logging.WARNING)
logging.getLogger("strands").setLevel(logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# Callback Handler
# =============================================================================


class StreamingProgressHandler:
    """Emit progress events during multi-agent A2A orchestration.

    Callback handler that receives various event types from Strands agent execution:
    - `data`: Streaming text chunks during model response generation
    - `current_tool_use`: Partial tool call data (fires repeatedly as tokens stream)
    - `message`: Complete message after generation (role=assistant or user)
    - `complete`: Final event when full response is ready

    De-duplication strategy:
    Tool invocations may appear multiple times in the event stream when conversation
    history is replayed for context. Tracking toolUseId values ensures each tool
    execution is logged exactly once, maintaining a clear audit trail in CloudWatch.
    """

    def __init__(self) -> None:
        self.progress_shown_ids: set[str] = set()
        self.logged_tool_ids: set[str] = set()

    def __call__(self, **kwargs: Any) -> None:
        # Show progress immediately when tool name arrives
        current_tool_use = kwargs.get("current_tool_use", {})
        if current_tool_use and current_tool_use.get("name"):
            tool_id = current_tool_use.get("toolUseId")
            tool_name = current_tool_use.get("name", "")

            if tool_id and tool_id not in self.progress_shown_ids:
                self.progress_shown_ids.add(tool_id)

                if "a2a_send_message" in tool_name:
                    print("\n[Calling agent...]", flush=True)
                elif "a2a_list" in tool_name:
                    print("\n[Discovering available agents...]", flush=True)

        # Log routing decisions after tool input is complete
        message = kwargs.get("message", {})
        if not isinstance(message, dict):
            return

        if message.get("role") == "assistant":
            for content in message.get("content", []):
                if isinstance(content, dict):
                    tool_use = content.get("toolUse")
                    if tool_use:
                        tool_id = tool_use.get("toolUseId")
                        if tool_id and tool_id not in self.logged_tool_ids:
                            self.logged_tool_ids.add(tool_id)
                            tool_name = tool_use.get("name", "")
                            tool_input = tool_use.get("input", {})

                            if "a2a_send_message" in tool_name:
                                input_str = str(tool_input).lower()
                                if "order" in input_str:
                                    logger.info("Routing to Order Agent")
                                elif "product" in input_str:
                                    logger.info("Routing to Product Agent")

        # Handle tool results
        elif message.get("role") == "user":
            for content in message.get("content", []):
                if isinstance(content, dict) and "toolResult" in content:
                    status = content["toolResult"].get("status", "")
                    if status == "success":
                        print("[Agent response received]", flush=True)
                    elif status == "error":
                        print("[Agent error]", flush=True)


# =============================================================================
# Configuration
# =============================================================================

SYSTEM_PROMPT = """You are the E-commerce Shopping Assistant Orchestrator.

Route customer queries to the Order Agent (order status, history) or Product Agent (catalog, browsing).
For queries needing both, call Order Agent first to get product_ids, then Product Agent for details.
Respond in a friendly, personalized way."""

# =============================================================================
# Tools
# =============================================================================


@tool(context=True)
def get_customer_context(tool_context: ToolContext) -> dict:
    """Retrieve current customer context including customer ID from session state.

    Enables orchestrator to access session-level state (customer_id) set during
    invocation. Specialist agents use this context to filter results appropriately.

    Args:
        tool_context: Strands ToolContext containing invocation_state dictionary.

    Returns:
        Dictionary with customer_id from session state or "unknown" as fallback.
    """
    return {"customer_id": tool_context.invocation_state.get("customer_id", "unknown")}


# =============================================================================
# Agent Creation
# =============================================================================


def create_orchestrator(order_agent_url: str, product_agent_url: str) -> Agent:
    """Create orchestrator agent with A2A client tools for multi-agent orchestration.

    Configures agent with A2AClientToolProvider to communicate with specialist agents
    deployed to Amazon Bedrock AgentCore. A2A protocol (JSON-RPC 2.0 based) enables
    standardized agent discovery via Agent Cards and inter-agent communication.

    Args:
        order_agent_url: Amazon Bedrock AgentCore invocation URL for Order Agent.
        product_agent_url: Amazon Bedrock AgentCore invocation URL for Product Agent.

    Returns:
        Configured Agent instance ready to orchestrate multi-agent workflows.
    """
    logger.info(f"Initializing A2A client for Order Agent: {order_agent_url}")
    logger.info(f"Initializing A2A client for Product Agent: {product_agent_url}")

    session = boto3.Session()
    region = session.region_name or "us-west-2"
    credentials = session.get_credentials()

    logger.info(f"Using AWS region: {region}")

    # Configure SigV4 authentication for A2A protocol calls
    auth = SigV4HTTPXAuth(
        credentials=credentials,
        service="bedrock-agentcore",
        region=region,
    )

    logger.info("AWS SigV4 authentication configured for A2A protocol")

    # A2AClientToolProvider discovers agent capabilities from Agent Cards
    a2a_provider = A2AClientToolProvider(
        known_agent_urls=[order_agent_url, product_agent_url],
        httpx_client_args={"auth": auth},
    )

    logger.info(f"A2A client tools available: {len(a2a_provider.tools)} tools")

    agent = Agent(
        name="Ecommerce_Shopping_Orchestrator",
        description="Coordinates customer shopping queries using Order and Product agents",
        system_prompt=SYSTEM_PROMPT,
        model=BedrockModel(model_id="us.anthropic.claude-sonnet-4-20250514-v1:0", region_name=region),
        tools=[get_customer_context] + a2a_provider.tools,
        callback_handler=StreamingProgressHandler(),
    )

    logger.info(f"Agent created: {agent.name}")

    return agent
