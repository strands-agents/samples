"""A single MCP server exposed over Streamable HTTP.

Run it standalone so the agent's ``MCPClient`` can connect and load its tools
at startup:

    python -m mcp_server.server

It listens on ``http://<host>:<port>/mcp`` (default ``http://localhost:8001/mcp``)
and exposes a small in-memory knowledge base so the agent can look up
company-specific facts that are not in the model's training data. This
demonstrates how MCP tools compose with the agent's local tools.

Configure host/port via ``MCP_HOST`` / ``MCP_PORT`` environment variables.
"""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

HOST = os.environ.get("MCP_HOST", "localhost")
PORT = int(os.environ.get("MCP_PORT", "8001"))

mcp = FastMCP("knowledge-base", host=HOST, port=PORT)

# A tiny in-memory "knowledge base" standing in for a real backend.
_FAQ: dict[str, str] = {
    "support_hours": "Support is available Monday to Friday, 9am-6pm US Eastern time.",
    "return_policy": "Items can be returned within 30 days of purchase with a receipt.",
    "shipping_time": "Standard shipping takes 3-5 business days; express takes 1-2.",
}


@mcp.tool()
def lookup_faq(topic: str) -> str:
    """Look up a company FAQ answer by topic.

    Args:
        topic: One of "support_hours", "return_policy", "shipping_time".

    Returns:
        The FAQ answer, or a message listing valid topics.
    """
    answer = _FAQ.get(topic)
    if answer is None:
        return f"Unknown topic '{topic}'. Valid topics: {', '.join(sorted(_FAQ))}."
    return answer


@mcp.tool()
def list_faq_topics() -> list[str]:
    """List the available FAQ topics that ``lookup_faq`` can answer."""
    return sorted(_FAQ)


if __name__ == "__main__":
    # Streamable HTTP transport serves the MCP endpoint at /mcp.
    mcp.run(transport="streamable-http")
