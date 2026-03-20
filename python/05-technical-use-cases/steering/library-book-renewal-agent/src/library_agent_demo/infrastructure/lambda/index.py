"""
Lambda function handler for the library book renewal tool.

This function implements the renew_book tool that:
1. Validates input parameters
2. Calculates new due date based on renewal period
3. Returns renewal result with success status

When used as an AgentCore Gateway Lambda target, the function receives
tool arguments directly in the event object, not MCP protocol messages.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any

# Configure logging
log_level = os.environ.get("LOG_LEVEL", "INFO")
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda handler for AgentCore Gateway tool invocation.

    Args:
        event: Tool arguments (book, renewal_period, library_card_number)
        context: Lambda context with AgentCore metadata

    Returns:
        Tool execution result
    """
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        logger.info(f"Context type: {type(context)}")

        # Extract tool name from context if available
        tool_name = None
        if hasattr(context, "client_context") and context.client_context:
            custom_data = getattr(context.client_context, "custom", {})
            logger.info(f"Custom context data: {custom_data}")
            full_tool_name = custom_data.get("bedrockAgentCoreToolName", "")
            if full_tool_name:
                # Strip target prefix from tool name (format: target___tool_name)
                delimiter = "___"
                if delimiter in full_tool_name:
                    tool_name = full_tool_name[full_tool_name.index(delimiter) + len(delimiter) :]
                else:
                    tool_name = full_tool_name
                logger.info(f"Extracted tool name: {tool_name}")

        # If no tool name from context, assume it's renew_book (for direct invocation)
        if not tool_name:
            tool_name = "renew_book"
            logger.info(f"No tool name in context, defaulting to: {tool_name}")

        logger.info(f"Processing tool: {tool_name}")

        # Route to appropriate tool handler
        if tool_name == "renew_book":
            return renew_book(event)
        else:
            logger.error(f"Unknown tool: {tool_name}")
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
                "message": f"Tool '{tool_name}' is not supported by this Lambda function",
            }

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to process renewal request: {str(e)}",
        }


def renew_book(event: dict[str, Any]) -> dict[str, Any]:
    """
    Handle the book renewal request.

    Args:
        event: Tool arguments containing book, renewal_period, library_card_number

    Returns:
        Renewal result with success status and new due date
    """
    try:
        # Extract and validate required arguments
        book = event.get("book")
        renewal_period = event.get("renewal_period")
        library_card_number = event.get("library_card_number")

        # Validate required fields
        if not book:
            return {
                "success": False,
                "error": "Missing required argument: book",
                "message": "Book identifier is required for renewal",
            }

        if not renewal_period:
            return {
                "success": False,
                "error": "Missing required argument: renewal_period",
                "message": "Renewal period is required",
            }

        if not library_card_number:
            return {
                "success": False,
                "error": "Missing required argument: library_card_number",
                "message": "Library card number is required",
            }

        # Validate renewal period type and minimum value
        if not isinstance(renewal_period, int) or renewal_period < 1:
            return {
                "success": False,
                "error": "Invalid renewal period",
                "message": "Renewal period must be a positive integer",
            }

        # Calculate new due date
        current_date = datetime.now()
        new_due_date = current_date + timedelta(days=renewal_period)

        # Create successful response
        result = {
            "success": True,
            "book": book,
            "library_card_number": library_card_number,
            "renewal_period": renewal_period,
            "new_due_date": new_due_date.isoformat(),
            "formatted_due_date": new_due_date.strftime("%Y-%m-%d"),
            "message": (
                f"Book '{book}' successfully renewed for {renewal_period} days. "
                f"New due date: {new_due_date.strftime('%Y-%m-%d')}"
            ),
        }

        logger.info(f"Successfully renewed book: {result}")
        return result

    except Exception as e:
        logger.error(f"Error in renew_book: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to renew book: {str(e)}",
        }
