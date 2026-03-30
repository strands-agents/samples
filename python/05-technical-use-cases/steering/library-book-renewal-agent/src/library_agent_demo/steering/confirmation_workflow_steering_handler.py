"""Confirmation steering handler for workflow validation and enforcement.

This handler provides both tool-level and model-level steering to ensure:
1. Confirmations are only sent after successful renewals (tool steering)
2. Confirmations are sent before final response (model steering)
"""

import logging
from typing import TYPE_CHECKING, Any, Literal

from strands.types.content import Message
from strands.types.tools import ToolUse
from strands.vended_plugins.steering import (
    Guide,
    ModelSteeringAction,
    Proceed,
    SteeringContextProvider,
    SteeringHandler,
    ToolSteeringAction,
)

if TYPE_CHECKING:
    from strands import Agent

logger = logging.getLogger(__name__)


class ConfirmationWorkflowSteeringHandler(SteeringHandler):
    """Steering handler for confirmation message workflow validation and enforcement.

    This handler provides two levels of control:
    1. Tool steering (steer_before_tool): Blocks send_confirmation calls without prior successful renewal
    2. Model steering (steer_after_model): Ensures confirmations are sent before final response
    """

    name = "confirmation_workflow_steering"

    def __init__(self, context_providers: list[SteeringContextProvider] | None = None) -> None:
        """Initialize the confirmation steering handler."""
        from strands.vended_plugins.steering import LedgerProvider

        providers = context_providers or [LedgerProvider()]
        super().__init__(context_providers=providers)
        logger.info("ConfirmationWorkflowSteeringHandler initialized")

    async def steer_before_tool(self, *, agent: Any, tool_use: ToolUse, **kwargs: Any) -> ToolSteeringAction:
        """Validate that confirmation messages are only sent after successful renewals.

        Args:
            agent: The agent attempting the tool call
            tool_use: The tool use being attempted
            **kwargs: Additional keyword arguments

        Returns:
            ToolSteeringAction indicating whether to proceed or block the tool call
        """
        tool_name = tool_use.get("name")

        # Only intercept send_confirmation tool calls
        if tool_name != "send_confirmation":
            return Proceed(reason="Not a confirmation tool call")

        # Get ledger data from context
        context_data = self.steering_context.data.get() or {}
        ledger = context_data.get("ledger", {})
        tool_calls = ledger.get("tool_calls", [])

        # Get the book_id from the confirmation input
        tool_input = tool_use.get("input", {})
        confirmation_book_id = tool_input.get("book_id")

        logger.debug(f"Checking confirmation for book_id={confirmation_book_id}")

        # Check if there was a successful renewal for this specific book
        successful_renewal = False
        for call in tool_calls:
            tool_name = call.get("tool_name", "")
            # Check for renewal tool (gateway or local)
            is_renewal = "renew_book" in tool_name.lower() or "renew-book" in tool_name.lower()
            if is_renewal and call.get("status") == "success":
                # Try different possible parameter names
                renewal_book_id = call.get("tool_args", {}).get("book") or call.get("tool_args", {}).get("book_id")
                if renewal_book_id == confirmation_book_id:
                    successful_renewal = True
                    logger.debug(f"Found matching renewal for book {confirmation_book_id} using tool {tool_name}")
                    break

        if not successful_renewal:
            logger.warning(
                f"Blocking send_confirmation call - no successful renewal found for book {confirmation_book_id}"
            )
            return Guide(
                reason=f"Tool call cancelled. Cannot send confirmation message for book {confirmation_book_id} "
                "without a successful renewal for that book. "
                "Please complete the book renewal first, then retry the send_confirmation tool."
            )

        logger.info("Allowing send_confirmation call - successful renewal found")
        return Proceed(reason="Tool call allowed to proceed")

    async def steer_after_model(
        self,
        *,
        agent: "Agent",
        message: Message,
        stop_reason: Literal[
            "content_filtered",
            "end_turn",
            "guardrail_intervened",
            "interrupt",
            "max_tokens",
            "stop_sequence",
            "tool_use",
        ],
        **kwargs: Any,
    ) -> ModelSteeringAction:
        """Ensure confirmation is sent after successful renewal before final response.

        Args:
            agent: The agent instance
            message: The model's generated message
            stop_reason: The reason the model stopped generating
            **kwargs: Additional keyword arguments

        Returns:
            ModelSteeringAction indicating whether to proceed or guide
        """
        logger.debug(f"steer_after_model called with stop_reason={stop_reason}")

        # Only check on end_turn (final response)
        if stop_reason != "end_turn":
            logger.debug(f"Not a final response (stop_reason={stop_reason}), proceeding")
            return Proceed(reason="Not a final response")

        # Get ledger data from context
        context_data = self.steering_context.data.get() or {}
        ledger = context_data.get("ledger", {})
        tool_calls = ledger.get("tool_calls", [])

        logger.info(f"steer_after_model: Checking ledger with {len(tool_calls)} tool calls")

        # Find successful renewals
        renewed_book_ids = set()
        for call in tool_calls:
            tool_name = call.get("tool_name", "")
            # Check for renewal tool (gateway or local)
            is_renewal = "renew_book" in tool_name.lower() or "renew-book" in tool_name.lower()
            if is_renewal and call.get("status") == "success":
                # Try different possible parameter names
                book_id = call.get("tool_args", {}).get("book") or call.get("tool_args", {}).get("book_id")
                if book_id:
                    renewed_book_ids.add(book_id)
                    logger.info(f"Found successful renewal for book_id={book_id} using tool={tool_name}")

        if not renewed_book_ids:
            logger.info("No successful renewals found, proceeding")
            return Proceed(reason="No successful renewals to confirm")

        # Find confirmed book IDs (only successful confirmations)
        confirmed_book_ids = set()
        for call in tool_calls:
            if call.get("tool_name") == "send_confirmation" and call.get("status") == "success":
                book_id = call.get("tool_args", {}).get("book_id")
                if book_id:
                    confirmed_book_ids.add(book_id)
                    logger.info(f"Found successful confirmation for book_id={book_id}")
            elif call.get("tool_name") == "send_confirmation":
                # Log non-successful confirmation attempts for debugging
                status = call.get("status", "unknown")
                book_id = call.get("tool_args", {}).get("book_id")
                logger.info(f"Found confirmation with status={status} for book_id={book_id}")

        # Check if any renewals are missing confirmations
        unconfirmed_book_ids = renewed_book_ids - confirmed_book_ids

        logger.info(
            f"Renewed books: {renewed_book_ids}, Confirmed books: {confirmed_book_ids}, "
            f"Unconfirmed: {unconfirmed_book_ids}"
        )

        if unconfirmed_book_ids:
            book_list = ", ".join(unconfirmed_book_ids)
            guidance = (
                f"Your previous response was NOT shown to the user. "
                f"You successfully renewed book(s) {book_list} but have not sent confirmation messages yet. "
                "You must use the send_confirmation tool for each renewed book before providing your final response. "
                "Send the confirmation messages now."
            )
            logger.info(f"Model guidance: {guidance}")
            return Guide(reason=guidance)

        return Proceed(reason="All renewals have confirmations")
