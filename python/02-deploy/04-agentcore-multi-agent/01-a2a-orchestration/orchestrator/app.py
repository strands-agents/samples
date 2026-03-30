"""Orchestrator application deployed to Amazon Bedrock AgentCore with HTTP protocol.

Multi-agent orchestrator that routes customer queries to Order and Product specialist
agents via A2A protocol. Demonstrates BedrockAgentCoreApp integration pattern for
HTTP protocol deployments with streaming event processing.

Key features:
- BedrockAgentCoreApp for Amazon Bedrock AgentCore HTTP protocol integration
- OpenTelemetry instrumentation for AWS X-Ray distributed tracing
- AWS Systems Manager Parameter Store for centralized agent URL configuration
- Structured event filtering for rich client-side streaming visualization
"""

import logging
import os
from datetime import datetime

import boto3
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.telemetry import StrandsTelemetry

from agent import create_orchestrator

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

SSM_ORDER_AGENT_URL = "/ecommerce-assistant/order-agent-url"
SSM_PRODUCT_AGENT_URL = "/ecommerce-assistant/product-agent-url"

logger.info("=" * 60)
logger.info("=== Shopping Assistant Orchestrator Initialization ===")
logger.info("=" * 60)

# =============================================================================
# Agent Runtime Initialization
# =============================================================================

app = BedrockAgentCoreApp()


def get_agent_url(ssm_param: str, env_var: str) -> str:
    """Retrieve agent invocation URL from environment or AWS Systems Manager.

    Checks environment variable first (useful for local development), then falls
    back to SSM Parameter Store (standard for Amazon Bedrock AgentCore deployments).

    Args:
        ssm_param: SSM parameter path (e.g., /ecommerce-assistant/order-agent-url).
        env_var: Environment variable name to check first.

    Returns:
        Amazon Bedrock AgentCore agent invocation URL for A2A protocol calls.
    """
    if url := os.environ.get(env_var):
        logger.info(f"Using {env_var} from environment: {url}")
        return url
    logger.info(f"Reading URL from SSM: {ssm_param}")
    ssm = boto3.client("ssm")
    response = ssm.get_parameter(Name=ssm_param, WithDecryption=True)
    return response["Parameter"]["Value"]


# Initialize orchestrator at module level (created once on container start)
logger.info("Retrieving agent URLs from SSM...")
order_agent_url = get_agent_url(SSM_ORDER_AGENT_URL, "ORDER_AGENT_URL")
product_agent_url = get_agent_url(SSM_PRODUCT_AGENT_URL, "PRODUCT_AGENT_URL")
logger.info(f"Order Agent URL: {order_agent_url}")
logger.info(f"Product Agent URL: {product_agent_url}")

logger.info("Creating orchestrator with A2A client...")
orchestrator = create_orchestrator(order_agent_url, product_agent_url)
logger.info(f"Orchestrator created: {orchestrator.name}")
logger.info("=" * 60)
logger.info("=== Orchestrator Initialization Complete ===")
logger.info("=" * 60)

# =============================================================================
# Entry Point
# =============================================================================


@app.entrypoint
async def invoke(payload):
    """Invoke orchestrator agent with streaming response for multi-agent orchestration.

    Entry point called by Amazon Bedrock AgentCore when request arrives at runtime
    endpoint. Async streaming provides real-time progress updates as orchestrator
    orchestrates specialist agents.

    Args:
        payload: Request payload containing prompt and optional customer_id.

    Yields:
        Structured event dictionaries for client-side rendering.
    """
    user_input = payload.get("prompt", "")
    customer_id = payload.get("customer_id", "CUST-101")

    logger.info("=" * 60)
    logger.info("=== INCOMING REQUEST ===")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Customer: {customer_id}")
    logger.info(f"Prompt: {user_input}")
    logger.info("=" * 60)

    logger.info("Starting streaming response...")
    async for event in orchestrator.stream_async(user_input, customer_id=customer_id):
        if isinstance(event, dict):
            # Strands callback events
            if event.get("start_event_loop"):
                yield {"type": "thinking"}

            if "message" in event:
                msg = event["message"]
                if isinstance(msg, dict) and msg.get("role") == "user":
                    for content in msg.get("content", []):
                        if isinstance(content, dict) and "toolResult" in content:
                            status = content["toolResult"].get("status", "success")
                            yield {"type": "tool_result", "status": status}

            if "event_loop_throttled_delay" in event:
                yield {"type": "throttled", "seconds": event["event_loop_throttled_delay"]}

            if "reasoningText" in event:
                yield {"type": "reasoning", "content": event["reasoningText"]}

            # Amazon Bedrock streaming events
            if "event" in event:
                inner = event.get("event", {})

                if "messageStart" in inner:
                    yield {"type": "message_start"}

                elif "contentBlockStart" in inner:
                    start = inner["contentBlockStart"]
                    if "toolUse" in start.get("start", {}):
                        tool_info = start["start"]["toolUse"]
                        yield {
                            "type": "tool_start",
                            "name": tool_info.get("name", "unknown"),
                            "id": tool_info.get("toolUseId", ""),
                        }

                elif "contentBlockDelta" in inner:
                    delta = inner["contentBlockDelta"].get("delta", {})

                    if "text" in delta:
                        yield {"type": "text", "content": delta["text"]}

                    if "toolUse" in delta:
                        tool_input = delta["toolUse"].get("input", "")
                        yield {"type": "tool_input", "input": tool_input}

                elif "contentBlockStop" in inner:
                    yield {"type": "tool_complete"}

                elif "messageStop" in inner:
                    stop_reason = inner["messageStop"].get("stopReason", "")
                    yield {"type": "message_stop", "reason": stop_reason}

        elif isinstance(event, str):
            yield {"type": "text", "content": event}

    logger.info("=" * 60)
    logger.info("=== STREAMING COMPLETE ===")
    logger.info("=" * 60)


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    app.run()
