"""Agent callback handlers for observability and debugging.

Provides reusable callback handlers for logging tool execution events
during agent reasoning loops. Used across all agents in the multi-agent
tutorial for consistent CloudWatch Logs integration.

Key classes:
- ToolLoggingHandler: Log tool calls and completion events to CloudWatch Logs
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


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
    - Debug tool execution failures and input validation issues
    - Track external service calls (APIs, databases) in multi-agent workflows
    - Build custom observability dashboards on Amazon Bedrock AgentCore metrics

    Example:
        >>> agent = Agent(
        ...     name="MyAgent",
        ...     tools=[my_tool],
        ...     callback_handler=ToolLoggingHandler(),
        ... )
        >>> # Tool calls will be logged to CloudWatch with format:
        >>> # === TOOL #1: my_tool ===
        >>> # TOOL INPUT: {"param": "value"}
    """

    def __init__(self) -> None:
        self.logged_tool_ids: set[str] = set()  # Deduplicate tool logs
        self.tool_count = 0  # Sequential counter for log readability

    def __call__(self, **kwargs: Any) -> None:
        """Process agent lifecycle events and log tool executions.

        Args:
            **kwargs: Event data from Strands agent execution engine.
                message: Message dictionary with role and content.
                complete: Boolean indicating agent response completion.
                data: Response text data when complete=True.
        """
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
                            # Truncate input for very large payloads
                            input_str = json.dumps(tool_input)
                            if len(input_str) > 2000:
                                input_str = input_str[:2000] + "... (truncated)"
                            logger.info(f"TOOL INPUT: {input_str}")

        if kwargs.get("complete") and kwargs.get("data"):
            logger.info(f"=== COMPLETE: {len(kwargs.get('data', ''))} chars ===")
