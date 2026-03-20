"""Workflow steering handler for validating book renewal workflow adherence."""

import json
import logging
from typing import Any

from strands.types.tools import ToolUse
from strands.vended_plugins.steering import (
    Guide,
    Proceed,
    SteeringContextProvider,
    SteeringHandler,
    ToolSteeringAction,
)

logger = logging.getLogger(__name__)


def _extract_result_value(result: list[dict]) -> Any:
    """Extract tool result value from ledger content format [{"text": "JSON"}]."""
    if len(result) != 1:
        raise ValueError(f"Expected single content block, got {len(result)}")
    text = result[0].get("text", "")
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text


class RenewalWorkflowSteeringHandler(SteeringHandler):
    """Steering handler for workflow adherence and input validation.

    This handler ensures that:
    1. Book status is checked before renewal attempts
    2. User info is retrieved before renewal attempts
    3. Books with RECALLED status are not renewed
    4. Library card numbers match the user's actual card number
    5. Book IDs match between status check and renewal
    """

    name = "renewal_workflow_steering"

    def __init__(self, context_providers: list[SteeringContextProvider] | None = None) -> None:
        """Initialize the workflow steering handler."""
        from strands.vended_plugins.steering import LedgerProvider

        providers = context_providers or [LedgerProvider()]
        super().__init__(context_providers=providers)
        logger.info("RenewalWorkflowSteeringHandler initialized")

    async def steer_before_tool(self, *, agent: Any, tool_use: ToolUse, **kwargs: Any) -> ToolSteeringAction:
        """Provide steering guidance for workflow adherence and input validation.

        Args:
            agent: The agent attempting the tool call
            tool_use: The tool use being attempted
            **kwargs: Additional keyword arguments

        Returns:
            ToolSteeringAction indicating whether to proceed or provide guidance
        """
        tool_name = tool_use.get("name")

        # Get ledger data from context
        context_data = self.steering_context.data.get() or {}
        ledger = context_data.get("ledger", {})
        tool_calls = ledger.get("tool_calls", [])

        # Only validate renewal attempts
        if tool_name != "renewal-server-target___renew_book":
            return Proceed(reason="Not a renewal tool call")

        logger.info(f"Renewal workflow check: Found {len(tool_calls)} tool calls in ledger")
        for call in tool_calls:
            logger.info(f"  - {call.get('tool_name')} (status: {call.get('status')})")

        # Check if book status was checked (ignore pending entries - they were cancelled)
        book_status_checked = any(
            call.get("tool_name") == "get_book_status" and call.get("status") == "success" for call in tool_calls
        )

        if not book_status_checked:
            guidance = (
                "Tool call cancelled. You must successfully check the book status before attempting to renew it. "
                "Please use the get_book_status tool first to ensure the book is available for renewal, "
                "then retry the renewal request."
            )
            logger.info(f"Workflow guidance: {guidance}")
            return Guide(reason=guidance)

        # Check if user info was retrieved
        user_info_retrieved = any(
            call.get("tool_name") == "get_user_info" and call.get("status") == "success" for call in tool_calls
        )

        if not user_info_retrieved:
            guidance = (
                "Tool call cancelled. You must successfully retrieve user information before attempting to renew. "
                "Please use the get_user_info tool first to get the library card number, "
                "then retry the renewal request."
            )
            logger.info(f"Workflow guidance: {guidance}")
            return Guide(reason=guidance)

        # Check if book status is RECALLED (use last successful check)
        book_status = None
        for call in tool_calls:
            if call.get("tool_name") == "get_book_status" and call.get("status") == "success":
                result = _extract_result_value(call.get("result"))
                if isinstance(result, dict):
                    book_status = result.get("status")
        if book_status == "RECALLED":
            guidance = (
                "Tool call cancelled. Cannot renew a book with RECALLED status. "
                "Books that have been recalled by the library cannot be renewed. "
                "Inform the user that the book cannot be renewed because it has been recalled."
            )
            logger.info(f"Workflow guidance: {guidance}")
            return Guide(reason=guidance)

        # Validate renewal request parameters
        tool_input = tool_use.get("input", {})
        renewal_card_number = tool_input.get("library_card_number")
        renewal_book_id = tool_input.get("book") or tool_input.get("book_id")

        # Validate library card number
        if renewal_card_number:
            user_card_number = None
            for call in tool_calls:
                if call.get("tool_name") == "get_user_info" and call.get("status") == "success":
                    result = _extract_result_value(call.get("result"))
                    if isinstance(result, dict):
                        user_card_number = result.get("library_card_number")

            if not user_card_number:
                guidance = (
                    "Tool call cancelled. You must successfully retrieve the user's library card number "
                    "before attempting to renew. "
                    "Please call the get_user_info tool again to get the library card number, "
                    "then retry the renewal request."
                )
                logger.info(f"Workflow guidance: {guidance}")
                return Guide(reason=guidance)

            if renewal_card_number != user_card_number:
                guidance = (
                    f"Tool call cancelled. Library card number mismatch detected. "
                    f"You provided '{renewal_card_number}' but the user's actual library card number "
                    f"is '{user_card_number}'. Retry the renewal request using the correct card: {user_card_number}"
                )
                logger.info(f"Input validation guidance: {guidance}")
                return Guide(reason=guidance)

        # Validate book ID matches the book status check
        if renewal_book_id:
            checked_book_id = None
            for call in tool_calls:
                if call.get("tool_name") == "get_book_status" and call.get("status") == "success":
                    call_args = call.get("tool_args", {})
                    if isinstance(call_args, dict):
                        checked_book_id = call_args.get("book_id")

            if not checked_book_id:
                guidance = (
                    "Tool call cancelled. You must successfully retrieve the book status "
                    "before attempting to renew it. "
                    "Please use the get_book_status tool again to ensure the book is available for renewal, "
                    "then retry the renewal request."
                )
                logger.info(f"Workflow guidance: {guidance}")
                return Guide(reason=guidance)

            if renewal_book_id != checked_book_id:
                guidance = (
                    f"Tool call cancelled. Book ID mismatch detected. "
                    f"You are attempting to renew book '{renewal_book_id}' but you checked the status "
                    f"of book '{checked_book_id}'. Please check the status of the book you intend to renew, "
                    "then retry the renewal request."
                )
                logger.info(f"Input validation guidance: {guidance}")
                return Guide(reason=guidance)

        return Proceed(reason="Workflow and input validation passed")
