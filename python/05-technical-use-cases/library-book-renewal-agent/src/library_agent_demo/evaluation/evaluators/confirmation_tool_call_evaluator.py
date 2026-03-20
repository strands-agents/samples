"""Confirmation tool call evaluator for library agent behavior assessment."""

# pyright: reportIncompatibleMethodOverride=false, reportOptionalMemberAccess=false

import json

from strands_evals.evaluators import Evaluator
from strands_evals.types import EvaluationData, EvaluationOutput

from ...models import ExpectedInputs
from .utils import extract_tools_from_output


class ConfirmationToolCallEvaluator(Evaluator[str, dict]):
    """Evaluates whether confirmation tool calls follow proper workflow requirements.

    Only evaluates successful confirmation calls (non-error).
    Steering can catch and fail bad inputs, so we only validate calls that actually succeeded.

    Validates that:
    1. Confirmation calls are only made after successful book renewal calls
    2. Confirmation calls use the correct book ID matching the renewed book
    """

    def __init__(self, expected_inputs: ExpectedInputs):
        """Initialize evaluator with expected inputs.

        Args:
            expected_inputs: ExpectedInputs with expected book_id
        """
        self.expected_inputs = expected_inputs

    def _get_successful_renewals(self, tools_used: list[dict]) -> list[dict]:
        """Extract successful renewal calls from tool list."""
        successful = []
        for tool in tools_used:
            if "renew_book" not in tool.get("name", "").lower():
                continue
            if tool.get("is_error", False):
                continue
            tool_result = tool.get("tool_result", "")
            if not tool_result:
                continue
            try:
                result_data = json.loads(tool_result)
                if result_data.get("success", False):
                    successful.append(tool)
            except (json.JSONDecodeError, AttributeError):
                pass
        return successful

    def _get_successful_confirmations(self, tools_used: list[dict]) -> list[dict]:
        """Extract successful confirmation calls from tool list."""
        return [
            tool
            for tool in tools_used
            if "send_confirmation" in tool.get("name", "").lower() and not tool.get("is_error", False)
        ]

    def evaluate(self, evaluation_case: EvaluationData[str, dict]) -> list[EvaluationOutput]:
        """Evaluate confirmation tool call workflow compliance."""
        try:
            output = evaluation_case.actual_output
            tools_used = extract_tools_from_output(output)

            successful_renewals = self._get_successful_renewals(tools_used)
            successful_confirmations = self._get_successful_confirmations(tools_used)

            # If there are successful renewals, confirmation is required
            if successful_renewals and not successful_confirmations:
                return [
                    EvaluationOutput(
                        score=0.0,
                        test_pass=False,
                        reason="Confirmation call required after successful renewal but not found",
                        label="missing_confirmation_after_renewal",
                    )
                ]

            # If no successful renewals, confirmation should not be made
            if not successful_renewals and successful_confirmations:
                return [
                    EvaluationOutput(
                        score=0.0,
                        test_pass=False,
                        reason="Confirmation call made without successful renewal",
                        label="confirmation_without_renewal",
                    )
                ]

            # If no successful renewals and no confirmation calls, pass
            if not successful_renewals and not successful_confirmations:
                return [
                    EvaluationOutput(
                        score=1.0,
                        test_pass=True,
                        reason="No successful renewals and no confirmation calls (correct)",
                        label="no_renewal_no_confirmation",
                    )
                ]

            # Check each confirmation call
            for confirmation_call in successful_confirmations:
                confirmation_input = confirmation_call.get("input", {})
                confirmation_book_id = confirmation_input.get("book_id", "")

                # Find successful renewal for this book
                successful_renewal_found = False
                for renewal_call in successful_renewals:
                    renewal_input = renewal_call.get("input", {})
                    renewal_book_id = renewal_input.get("book", "") or renewal_input.get("book_id", "")
                    if renewal_book_id == confirmation_book_id:
                        successful_renewal_found = True
                        break

                # Validate confirmation requirements
                if not successful_renewal_found:
                    successful_renewal_book_ids = []
                    for renewal_call in successful_renewals:
                        renewal_input = renewal_call.get("input", {})
                        renewal_book_id = renewal_input.get("book", "") or renewal_input.get("book_id", "")
                        if renewal_book_id:
                            successful_renewal_book_ids.append(renewal_book_id)

                    reason = f"Confirmation sent for book {confirmation_book_id} without successful renewal"
                    label = "confirmation_without_renewal"
                    if successful_renewal_book_ids:
                        reason += f". Successful renewals for: {', '.join(successful_renewal_book_ids)}"
                        label = "tool_input_mismatch"

                    return [
                        EvaluationOutput(
                            score=0.0,
                            test_pass=False,
                            reason=reason,
                            label=label,
                        )
                    ]

                # Validate book ID matches expected
                expected_book_id = self.expected_inputs.book_id
                if expected_book_id and confirmation_book_id != expected_book_id:
                    return [
                        EvaluationOutput(
                            score=0.0,
                            test_pass=False,
                            reason=f"Confirmation used incorrect book ID: {confirmation_book_id}, "
                            f"expected: {expected_book_id}",
                            label="incorrect_confirmation_book_id",
                        )
                    ]

            # All confirmation calls passed validation
            return [
                EvaluationOutput(
                    score=1.0,
                    test_pass=True,
                    reason="All confirmation calls follow proper workflow requirements",
                    label="confirmation_workflow_valid",
                )
            ]

        except Exception as e:
            return [
                EvaluationOutput(
                    score=0.0,
                    test_pass=False,
                    reason=f"Error evaluating confirmation workflow: {str(e)}",
                    label="evaluation_error",
                )
            ]
