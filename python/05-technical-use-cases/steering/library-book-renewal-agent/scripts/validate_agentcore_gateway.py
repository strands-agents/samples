#!/usr/bin/env python3
"""Validate the provisioned AgentCore Gateway - OAuth connection, tools, and policy enforcement."""

import logging
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from library_agent_demo.oauth_mcp_client import create_oauth_mcp_client, get_full_tools_list

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_oauth_connection(mcp_client) -> bool:
    """Test OAuth connection by listing tools."""
    logger.info("Testing OAuth connection...")
    tools = get_full_tools_list(mcp_client)
    logger.info(f"Connected! Found {len(tools)} tools:")
    for tool in tools:
        logger.info(f"  - {tool.tool_name}: {tool.mcp_tool.description}")
    return len(tools) > 0


def validate_policy_enforcement(mcp_client) -> bool:
    """Test that AgentCore Policy blocks requests > 30 days."""
    logger.info("\nTesting policy enforcement...")

    tools = get_full_tools_list(mcp_client)
    renewal_tool_name = next(
        (t.tool_name for t in tools if "renew" in t.tool_name.lower()),
        "renewal-server-target___renew_book",
    )
    logger.info(f"Using tool: {renewal_tool_name}")

    # Test valid request (30 days)
    logger.info("Testing valid request (30 days)...")
    try:
        result = mcp_client.call_tool_sync(
            tool_use_id="test-30-day",
            name=renewal_tool_name,
            arguments={"book": "test-book-123", "renewal_period": 30, "library_card_number": "123-456-789"},
        )
        if result.get("status") == "error" and "policy enforcement" in str(result.get("content", "")):
            logger.error(f"30-day request unexpectedly blocked: {result}")
            return False
        logger.info("30-day request succeeded as expected")
    except Exception as e:
        if "policy enforcement" in str(e):
            logger.error(f"30-day request unexpectedly blocked: {e}")
            return False
        logger.error(f"30-day request failed: {e}")
        return False

    # Test invalid request (90 days) - should be blocked
    logger.info("Testing invalid request (90 days)...")
    try:
        result = mcp_client.call_tool_sync(
            tool_use_id="test-90-day",
            name=renewal_tool_name,
            arguments={"book": "test-book-123", "renewal_period": 90, "library_card_number": "123-456-789"},
        )
        if result.get("status") == "error" and "policy enforcement" in str(result.get("content", "")):
            logger.info("90-day request correctly blocked by policy")
            return True
        logger.error(f"90-day request unexpectedly succeeded: {result}")
        return False
    except Exception as e:
        if "policy enforcement" in str(e):
            logger.info("90-day request correctly blocked by policy")
            return True
        logger.error(f"90-day request failed unexpectedly: {e}")
        return False


def main():
    """Run all gateway validations."""
    try:
        mcp_client = create_oauth_mcp_client()
        with mcp_client:
            if not validate_oauth_connection(mcp_client):
                return False
            if not validate_policy_enforcement(mcp_client):
                return False
        logger.info("\n✅ All gateway validations passed!")
        return True
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
