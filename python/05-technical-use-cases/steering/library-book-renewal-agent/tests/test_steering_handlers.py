"""Unit tests for steering handlers with various ledger state permutations."""

import pytest
from strands.experimental.steering import Guide, Proceed

from library_agent_demo.steering.confirmation_workflow_steering_handler import (
    ConfirmationWorkflowSteeringHandler,
)
from library_agent_demo.steering.renewal_workflow_steering_handler import (
    RenewalWorkflowSteeringHandler,
    _extract_result_value,
)


# --- Helper to build ledger state ---
def make_tool_call(
    tool_name: str, status: str, result: list[dict] | None = None, tool_args: dict | None = None
) -> dict:
    """Create a tool call entry for the ledger."""
    return {
        "tool_name": tool_name,
        "status": status,
        "result": result,
        "tool_args": tool_args or {},
    }


def make_ledger_content(data: dict) -> list[dict]:
    """Create ledger content format: [{"text": "JSON"}]."""
    import json

    return [{"text": json.dumps(data)}]


def make_user_info_result(card_number: str = "LIB-456789") -> list[dict]:
    """Create a user info result in ledger format."""
    return make_ledger_content({"name": "Alice", "account_number": "ACC-001", "library_card_number": card_number})


def make_book_status_result(book_id: str = "BOOK-123", status: str = "ACTIVE") -> list[dict]:
    """Create a book status result in ledger format."""
    return make_ledger_content({"book_id": book_id, "status": status})


def make_renewal_tool_use(book_id: str = "BOOK-123", card_number: str = "LIB-456789", period: int = 14) -> dict:
    """Create a renewal tool use request."""
    return {
        "name": "renewal-server-target___renew_book",
        "input": {"book": book_id, "library_card_number": card_number, "renewal_period": period},
    }


def make_confirmation_tool_use(book_id: str = "BOOK-123", message: str = "Renewed!") -> dict:
    """Create a confirmation tool use request."""
    return {
        "name": "send_confirmation",
        "input": {"book_id": book_id, "message": message},
    }


# --- Tests for _extract_result_value ---
class TestExtractResultValue:
    def test_text_json_content_block(self):
        """Ledger format with JSON string in text block."""
        result = [{"text": '{"name": "Alice", "library_card_number": "LIB-123"}'}]
        assert _extract_result_value(result) == {"name": "Alice", "library_card_number": "LIB-123"}

    def test_text_non_json_content_block(self):
        """Ledger format with non-JSON text."""
        result = [{"text": "plain text result"}]
        assert _extract_result_value(result) == "plain text result"

    def test_empty_list_raises(self):
        """Empty list raises error."""
        with pytest.raises(ValueError, match="Expected single content block"):
            _extract_result_value([])


# --- Tests for RenewalWorkflowSteeringHandler ---
class TestRenewalWorkflowSteeringHandler:
    @pytest.fixture
    def handler(self):
        return RenewalWorkflowSteeringHandler(context_providers=[])

    def set_ledger(self, handler: RenewalWorkflowSteeringHandler, tool_calls: list[dict]):
        """Set the ledger state on the handler."""
        handler.steering_context.data.set("ledger", {"tool_calls": tool_calls})

    @pytest.mark.asyncio
    async def test_non_renewal_tool_proceeds(self, handler):
        """Non-renewal tools should always proceed."""
        tool_use = {"name": "get_user_info", "input": {}}
        result = await handler.steer_before_tool(agent=None, tool_use=tool_use)
        assert isinstance(result, Proceed)

    @pytest.mark.asyncio
    async def test_no_book_status_check_blocks(self, handler):
        """Renewal without book status check should be blocked."""
        self.set_ledger(
            handler,
            [
                make_tool_call("get_user_info", "success", make_user_info_result()),
            ],
        )
        result = await handler.steer_before_tool(agent=None, tool_use=make_renewal_tool_use())
        assert isinstance(result, Guide)
        assert "check the book status" in result.reason

    @pytest.mark.asyncio
    async def test_no_user_info_blocks(self, handler):
        """Renewal without user info should be blocked."""
        self.set_ledger(
            handler,
            [
                make_tool_call("get_book_status", "success", make_book_status_result(), {"book_id": "BOOK-123"}),
            ],
        )
        result = await handler.steer_before_tool(agent=None, tool_use=make_renewal_tool_use())
        assert isinstance(result, Guide)
        assert "retrieve user information" in result.reason

    @pytest.mark.asyncio
    async def test_pending_status_ignored(self, handler):
        """Pending tool calls should be ignored (not count as successful)."""
        self.set_ledger(
            handler,
            [
                make_tool_call("get_book_status", "pending", make_book_status_result(), {"book_id": "BOOK-123"}),
                make_tool_call("get_user_info", "pending", make_user_info_result()),
            ],
        )
        result = await handler.steer_before_tool(agent=None, tool_use=make_renewal_tool_use())
        assert isinstance(result, Guide)
        assert "check the book status" in result.reason

    @pytest.mark.asyncio
    async def test_error_status_ignored(self, handler):
        """Error tool calls should be ignored."""
        self.set_ledger(
            handler,
            [
                make_tool_call("get_book_status", "error", None, {"book_id": "BOOK-123"}),
                make_tool_call("get_user_info", "error", None),
            ],
        )
        result = await handler.steer_before_tool(agent=None, tool_use=make_renewal_tool_use())
        assert isinstance(result, Guide)

    @pytest.mark.asyncio
    async def test_recalled_book_blocks(self, handler):
        """RECALLED book status should block renewal."""
        self.set_ledger(
            handler,
            [
                make_tool_call(
                    "get_book_status", "success", make_book_status_result(status="RECALLED"), {"book_id": "BOOK-123"}
                ),
                make_tool_call("get_user_info", "success", make_user_info_result()),
            ],
        )
        result = await handler.steer_before_tool(agent=None, tool_use=make_renewal_tool_use())
        assert isinstance(result, Guide)
        assert "RECALLED" in result.reason

    @pytest.mark.asyncio
    async def test_card_number_mismatch_blocks(self, handler):
        """Mismatched library card number should block renewal."""
        self.set_ledger(
            handler,
            [
                make_tool_call("get_book_status", "success", make_book_status_result(), {"book_id": "BOOK-123"}),
                make_tool_call("get_user_info", "success", make_user_info_result(card_number="LIB-CORRECT")),
            ],
        )
        tool_use = make_renewal_tool_use(card_number="LIB-WRONG")
        result = await handler.steer_before_tool(agent=None, tool_use=tool_use)
        assert isinstance(result, Guide)
        assert "mismatch" in result.reason.lower()
        assert "LIB-WRONG" in result.reason
        assert "LIB-CORRECT" in result.reason

    @pytest.mark.asyncio
    async def test_book_id_mismatch_blocks(self, handler):
        """Mismatched book ID should block renewal."""
        self.set_ledger(
            handler,
            [
                make_tool_call(
                    "get_book_status",
                    "success",
                    make_book_status_result(book_id="BOOK-OTHER"),
                    {"book_id": "BOOK-OTHER"},
                ),
                make_tool_call("get_user_info", "success", make_user_info_result()),
            ],
        )
        tool_use = make_renewal_tool_use(book_id="BOOK-123")
        result = await handler.steer_before_tool(agent=None, tool_use=tool_use)
        assert isinstance(result, Guide)
        assert "mismatch" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_valid_workflow_proceeds(self, handler):
        """Valid workflow with matching data should proceed."""
        self.set_ledger(
            handler,
            [
                make_tool_call("get_book_status", "success", make_book_status_result(), {"book_id": "BOOK-123"}),
                make_tool_call("get_user_info", "success", make_user_info_result()),
            ],
        )
        result = await handler.steer_before_tool(agent=None, tool_use=make_renewal_tool_use())
        assert isinstance(result, Proceed)

    @pytest.mark.asyncio
    async def test_multiple_book_status_uses_last_success(self, handler):
        """Multiple book status calls - should use last successful one."""
        self.set_ledger(
            handler,
            [
                make_tool_call(
                    "get_book_status", "success", make_book_status_result(status="RECALLED"), {"book_id": "BOOK-OLD"}
                ),
                make_tool_call(
                    "get_book_status", "success", make_book_status_result(status="ACTIVE"), {"book_id": "BOOK-123"}
                ),
                make_tool_call("get_user_info", "success", make_user_info_result()),
            ],
        )
        result = await handler.steer_before_tool(agent=None, tool_use=make_renewal_tool_use())
        assert isinstance(result, Proceed)

    @pytest.mark.asyncio
    async def test_multiple_book_status_last_recalled_blocks(self, handler):
        """Multiple book status calls - last one RECALLED should block."""
        self.set_ledger(
            handler,
            [
                make_tool_call(
                    "get_book_status", "success", make_book_status_result(status="ACTIVE"), {"book_id": "BOOK-123"}
                ),
                make_tool_call(
                    "get_book_status", "success", make_book_status_result(status="RECALLED"), {"book_id": "BOOK-123"}
                ),
                make_tool_call("get_user_info", "success", make_user_info_result()),
            ],
        )
        result = await handler.steer_before_tool(agent=None, tool_use=make_renewal_tool_use())
        assert isinstance(result, Guide)
        assert "recalled" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_multiple_user_info_uses_last_success(self, handler):
        """Multiple user info calls - should use last successful one."""
        self.set_ledger(
            handler,
            [
                make_tool_call("get_book_status", "success", make_book_status_result(), {"book_id": "BOOK-123"}),
                make_tool_call("get_user_info", "error", None),
                make_tool_call("get_user_info", "success", make_user_info_result(card_number="LIB-FIRST")),
                make_tool_call("get_user_info", "success", make_user_info_result(card_number="LIB-SECOND")),
            ],
        )
        tool_use = make_renewal_tool_use(card_number="LIB-SECOND")
        result = await handler.steer_before_tool(agent=None, tool_use=tool_use)
        assert isinstance(result, Proceed)

    @pytest.mark.asyncio
    async def test_order_independent(self, handler):
        """Tool call order shouldn't matter."""
        self.set_ledger(
            handler,
            [
                make_tool_call("get_user_info", "success", make_user_info_result()),
                make_tool_call("get_book_status", "success", make_book_status_result(), {"book_id": "BOOK-123"}),
            ],
        )
        result = await handler.steer_before_tool(agent=None, tool_use=make_renewal_tool_use())
        assert isinstance(result, Proceed)

    @pytest.mark.asyncio
    async def test_user_info_missing_card_number_blocks(self, handler):
        """User info without library_card_number should block."""
        self.set_ledger(
            handler,
            [
                make_tool_call("get_book_status", "success", make_book_status_result(), {"book_id": "BOOK-123"}),
                make_tool_call("get_user_info", "success", make_ledger_content({"name": "Alice"})),
            ],
        )
        result = await handler.steer_before_tool(agent=None, tool_use=make_renewal_tool_use())
        assert isinstance(result, Guide)
        assert "library card number" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_book_status_missing_book_id_blocks(self, handler):
        """Book status without book_id in args should block."""
        self.set_ledger(
            handler,
            [
                make_tool_call("get_book_status", "success", make_book_status_result(), {}),  # Missing book_id in args
                make_tool_call("get_user_info", "success", make_user_info_result()),
            ],
        )
        result = await handler.steer_before_tool(agent=None, tool_use=make_renewal_tool_use())
        assert isinstance(result, Guide)
        assert "book status" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_user_info_non_dict_result_blocks(self, handler):
        """User info with non-dict result should block."""
        self.set_ledger(
            handler,
            [
                make_tool_call("get_book_status", "success", make_book_status_result(), {"book_id": "BOOK-123"}),
                make_tool_call("get_user_info", "success", [{"text": "string result"}]),  # Non-JSON text
            ],
        )
        result = await handler.steer_before_tool(agent=None, tool_use=make_renewal_tool_use())
        assert isinstance(result, Guide)
        assert "library card number" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_parallel_calls_with_pending_ignored(self, handler):
        """Parallel tool calls with pending status should be ignored."""
        self.set_ledger(
            handler,
            [
                make_tool_call("get_book_status", "success", make_book_status_result(), {"book_id": "BOOK-123"}),
                make_tool_call("get_user_info", "success", make_user_info_result()),
                make_tool_call("get_checked_out_books", "pending", None),  # Parallel call still pending
                make_tool_call("renewal-server-target___renew_book", "pending", None, {"book": "BOOK-123"}),
            ],
        )
        result = await handler.steer_before_tool(agent=None, tool_use=make_renewal_tool_use())
        assert isinstance(result, Proceed)

    @pytest.mark.asyncio
    async def test_mixed_pending_and_success_uses_success(self, handler):
        """Should use successful calls even when pending calls exist for same tool."""
        self.set_ledger(
            handler,
            [
                make_tool_call("get_book_status", "pending", None, {"book_id": "BOOK-123"}),
                make_tool_call("get_book_status", "success", make_book_status_result(), {"book_id": "BOOK-123"}),
                make_tool_call("get_user_info", "pending", None),
                make_tool_call("get_user_info", "success", make_user_info_result()),
            ],
        )
        result = await handler.steer_before_tool(agent=None, tool_use=make_renewal_tool_use())
        assert isinstance(result, Proceed)

    @pytest.mark.asyncio
    async def test_only_pending_calls_blocks(self, handler):
        """Only pending calls (no success) should block."""
        self.set_ledger(
            handler,
            [
                make_tool_call("get_book_status", "pending", None, {"book_id": "BOOK-123"}),
                make_tool_call("get_user_info", "pending", None),
            ],
        )
        result = await handler.steer_before_tool(agent=None, tool_use=make_renewal_tool_use())
        assert isinstance(result, Guide)


# --- Tests for ConfirmationWorkflowSteeringHandler ---
class TestConfirmationWorkflowSteeringHandler:
    @pytest.fixture
    def handler(self):
        return ConfirmationWorkflowSteeringHandler(context_providers=[])

    def set_ledger(self, handler: ConfirmationWorkflowSteeringHandler, tool_calls: list[dict]):
        """Set the ledger state on the handler."""
        handler.steering_context.data.set("ledger", {"tool_calls": tool_calls})

    @pytest.mark.asyncio
    async def test_non_confirmation_tool_proceeds(self, handler):
        """Non-confirmation tools should always proceed."""
        tool_use = {"name": "get_user_info", "input": {}}
        result = await handler.steer_before_tool(agent=None, tool_use=tool_use)
        assert isinstance(result, Proceed)

    @pytest.mark.asyncio
    async def test_confirmation_without_renewal_blocks(self, handler):
        """Confirmation without prior renewal should be blocked."""
        self.set_ledger(handler, [])
        result = await handler.steer_before_tool(agent=None, tool_use=make_confirmation_tool_use())
        assert isinstance(result, Guide)
        assert "without a successful renewal" in result.reason

    @pytest.mark.asyncio
    async def test_confirmation_with_failed_renewal_blocks(self, handler):
        """Confirmation with only failed renewal should be blocked."""
        self.set_ledger(
            handler,
            [
                make_tool_call("renewal-server-target___renew_book", "error", None, {"book": "BOOK-123"}),
            ],
        )
        result = await handler.steer_before_tool(agent=None, tool_use=make_confirmation_tool_use())
        assert isinstance(result, Guide)

    @pytest.mark.asyncio
    async def test_confirmation_with_wrong_book_blocks(self, handler):
        """Confirmation for different book than renewed should be blocked."""
        self.set_ledger(
            handler,
            [
                make_tool_call("renewal-server-target___renew_book", "success", None, {"book": "BOOK-OTHER"}),
            ],
        )
        result = await handler.steer_before_tool(agent=None, tool_use=make_confirmation_tool_use(book_id="BOOK-123"))
        assert isinstance(result, Guide)

    @pytest.mark.asyncio
    async def test_confirmation_with_matching_renewal_proceeds(self, handler):
        """Confirmation with matching successful renewal should proceed."""
        self.set_ledger(
            handler,
            [
                make_tool_call("renewal-server-target___renew_book", "success", None, {"book": "BOOK-123"}),
            ],
        )
        result = await handler.steer_before_tool(agent=None, tool_use=make_confirmation_tool_use())
        assert isinstance(result, Proceed)

    @pytest.mark.asyncio
    async def test_confirmation_with_book_id_param(self, handler):
        """Renewal using book_id param instead of book."""
        self.set_ledger(
            handler,
            [
                make_tool_call("renewal-server-target___renew_book", "success", None, {"book_id": "BOOK-123"}),
            ],
        )
        result = await handler.steer_before_tool(agent=None, tool_use=make_confirmation_tool_use())
        assert isinstance(result, Proceed)

    @pytest.mark.asyncio
    async def test_steer_after_model_non_end_turn_proceeds(self, handler):
        """Non-end_turn stop reasons should proceed."""
        self.set_ledger(handler, [])
        result = await handler.steer_after_model(agent=None, message={}, stop_reason="tool_use")
        assert isinstance(result, Proceed)

    @pytest.mark.asyncio
    async def test_steer_after_model_no_renewals_proceeds(self, handler):
        """No renewals means no confirmation needed."""
        self.set_ledger(handler, [])
        result = await handler.steer_after_model(agent=None, message={}, stop_reason="end_turn")
        assert isinstance(result, Proceed)

    @pytest.mark.asyncio
    async def test_steer_after_model_unconfirmed_renewal_guides(self, handler):
        """Unconfirmed renewal should guide to send confirmation."""
        self.set_ledger(
            handler,
            [
                make_tool_call("renewal-server-target___renew_book", "success", None, {"book": "BOOK-123"}),
            ],
        )
        result = await handler.steer_after_model(agent=None, message={}, stop_reason="end_turn")
        assert isinstance(result, Guide)
        assert "BOOK-123" in result.reason
        assert "confirmation" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_steer_after_model_confirmed_renewal_proceeds(self, handler):
        """Confirmed renewal should proceed."""
        self.set_ledger(
            handler,
            [
                make_tool_call("renewal-server-target___renew_book", "success", None, {"book": "BOOK-123"}),
                make_tool_call("send_confirmation", "success", None, {"book_id": "BOOK-123"}),
            ],
        )
        result = await handler.steer_after_model(agent=None, message={}, stop_reason="end_turn")
        assert isinstance(result, Proceed)

    @pytest.mark.asyncio
    async def test_steer_after_model_partial_confirmation_guides(self, handler):
        """Multiple renewals with only some confirmed should guide."""
        self.set_ledger(
            handler,
            [
                make_tool_call("renewal-server-target___renew_book", "success", None, {"book": "BOOK-1"}),
                make_tool_call("renewal-server-target___renew_book", "success", None, {"book": "BOOK-2"}),
                make_tool_call("send_confirmation", "success", None, {"book_id": "BOOK-1"}),
            ],
        )
        result = await handler.steer_after_model(agent=None, message={}, stop_reason="end_turn")
        assert isinstance(result, Guide)
        assert "BOOK-2" in result.reason

    @pytest.mark.asyncio
    async def test_steer_after_model_failed_confirmation_not_counted(self, handler):
        """Failed confirmation should not count as confirmed."""
        self.set_ledger(
            handler,
            [
                make_tool_call("renewal-server-target___renew_book", "success", None, {"book": "BOOK-123"}),
                make_tool_call("send_confirmation", "error", None, {"book_id": "BOOK-123"}),
            ],
        )
        result = await handler.steer_after_model(agent=None, message={}, stop_reason="end_turn")
        assert isinstance(result, Guide)

    @pytest.mark.asyncio
    async def test_pending_renewal_not_counted(self, handler):
        """Pending renewal should not require confirmation."""
        self.set_ledger(
            handler,
            [
                make_tool_call("renewal-server-target___renew_book", "pending", None, {"book": "BOOK-123"}),
            ],
        )
        result = await handler.steer_after_model(agent=None, message={}, stop_reason="end_turn")
        assert isinstance(result, Proceed)

    @pytest.mark.asyncio
    async def test_parallel_renewals_with_pending(self, handler):
        """Parallel renewals - only successful ones need confirmation."""
        self.set_ledger(
            handler,
            [
                make_tool_call("renewal-server-target___renew_book", "success", None, {"book": "BOOK-1"}),
                make_tool_call("renewal-server-target___renew_book", "pending", None, {"book": "BOOK-2"}),
                make_tool_call("send_confirmation", "success", None, {"book_id": "BOOK-1"}),
            ],
        )
        result = await handler.steer_after_model(agent=None, message={}, stop_reason="end_turn")
        assert isinstance(result, Proceed)

    @pytest.mark.asyncio
    async def test_confirmation_with_pending_renewal_blocks(self, handler):
        """Confirmation for book with only pending renewal should block."""
        self.set_ledger(
            handler,
            [
                make_tool_call("renewal-server-target___renew_book", "pending", None, {"book": "BOOK-123"}),
            ],
        )
        result = await handler.steer_before_tool(agent=None, tool_use=make_confirmation_tool_use())
        assert isinstance(result, Guide)
