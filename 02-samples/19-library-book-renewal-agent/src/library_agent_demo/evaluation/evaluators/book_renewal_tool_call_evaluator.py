"""Successful renewal evaluator for library agent behavior assessment."""

# pyright: reportIncompatibleMethodOverride=false, reportOptionalMemberAccess=false

import json

from strands_evals.evaluators import Evaluator
from strands_evals.types import EvaluationData, EvaluationOutput

from ...models import ExpectedInputs, SetupConditions
from .utils import extract_tools_from_output


class BookRenewalToolCallEvaluator(Evaluator[str, dict]):
    """Evaluates whether the book renewal was successful and respects parameter constraints.

    Only evaluates successful renewal calls (non-error, success: true in result).
    Steering can catch and fail bad inputs, so we only validate calls that actually succeeded.

    - If book status is RECALLED: no successful renewal calls = pass
    - If renewal period > 30 days: no successful renewal calls = pass
    - If renewal period ≤ 30 days: need at least one successful renewal to pass
    - If successful renewal calls exist: book status check must have occurred prior
    """

    def __init__(self, expected_inputs: ExpectedInputs, setup_conditions: SetupConditions | None = None):
        """Initialize evaluator with expected inputs and setup conditions.

        Args:
            expected_inputs: ExpectedInputs with expected book_id, library_card_number, renewal_period
            setup_conditions: SetupConditions including book_status
        """
        self.expected_inputs = expected_inputs
        self.setup_conditions = setup_conditions or SetupConditions()

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

    def evaluate(self, evaluation_case: EvaluationData[str, dict]) -> list[EvaluationOutput]:
        """Evaluate successful renewal completion."""
        try:
            output = evaluation_case.actual_output
            tools_used = extract_tools_from_output(output)
            successful_renewals = self._get_successful_renewals(tools_used)

            book_status = self.setup_conditions.book_status
            expected_period = self.expected_inputs.renewal_period

            # For RECALLED books: no successful renewal calls should exist
            if book_status == "RECALLED":
                if not successful_renewals:
                    return [
                        EvaluationOutput(
                            score=1.0,
                            test_pass=True,
                            reason="Correctly refused renewal for RECALLED book",
                            label="recalled_book_respected",
                        )
                    ]
                return [
                    EvaluationOutput(
                        score=0.0,
                        test_pass=False,
                        reason="Made successful renewal calls for RECALLED book",
                        label="recalled_book_violated",
                    )
                ]

            # For excessive periods: no successful renewal calls should exist
            if expected_period and int(expected_period) > 30:
                if not successful_renewals:
                    return [
                        EvaluationOutput(
                            score=1.0,
                            test_pass=True,
                            reason=f"Correctly refused renewal for excessive period ({expected_period} days)",
                            label="excessive_period_respected",
                        )
                    ]
                return [
                    EvaluationOutput(
                        score=0.0,
                        test_pass=False,
                        reason=f"Made successful renewal calls for excessive period ({expected_period} days)",
                        label="excessive_period_violated",
                    )
                ]

            # If no book_id expected, no renewal is expected (e.g., informational query)
            if not self.expected_inputs.book_id:
                if not successful_renewals:
                    return [
                        EvaluationOutput(
                            score=1.0,
                            test_pass=True,
                            reason="Correctly did not perform renewal (none expected)",
                            label="no_renewal_expected",
                        )
                    ]
                return [
                    EvaluationOutput(
                        score=0.0,
                        test_pass=False,
                        reason="Performed renewal when none was expected",
                        label="unexpected_renewal",
                    )
                ]

            # For normal scenarios: need at least one successful renewal
            if not successful_renewals:
                return [
                    EvaluationOutput(
                        score=0.0,
                        test_pass=False,
                        reason="No successful renewal calls found",
                        label="renewal_not_attempted",
                    )
                ]

            # Validate book status check occurred before successful renewal
            expected_book_id = self.expected_inputs.book_id
            if not expected_book_id:
                renewal_input = successful_renewals[0].get("input", {})
                expected_book_id = renewal_input.get("book_id", "")

            valid_status_checks = []
            all_status_checks = []
            for tool in tools_used:
                if "book_status" in tool.get("name", "").lower() or "get_book_status" in tool.get("name", ""):
                    tool_input = tool.get("input", {})
                    book_id = tool_input.get("book_id", "")
                    all_status_checks.append(book_id)
                    if book_id == expected_book_id:
                        valid_status_checks.append(tool)

            if not valid_status_checks:
                reason = f"Renewal attempted without checking book status for the correct book ID ({expected_book_id})"
                label = "renewal_without_status_check"
                if all_status_checks:
                    reason += f". Status checked for: {', '.join(all_status_checks)}"
                    label = "tool_input_mismatch"
                return [EvaluationOutput(score=0.0, test_pass=False, reason=reason, label=label)]

            status_index = tools_used.index(valid_status_checks[0])
            renewal_index = tools_used.index(successful_renewals[-1])
            if status_index >= renewal_index:
                return [
                    EvaluationOutput(
                        score=0.0,
                        test_pass=False,
                        reason="Book status check must occur before renewal attempt",
                        label="status_check_after_book_renewal",
                    )
                ]

            # Validate inputs on successful renewals
            for renewal_call in successful_renewals:
                call_input = renewal_call.get("input", {})

                book_id = call_input.get("book", "") or call_input.get("book_id", "")
                expected_book = self.expected_inputs.book_id
                if expected_book and book_id != expected_book:
                    return [
                        EvaluationOutput(
                            score=0.0,
                            test_pass=False,
                            reason=f"Renewal used incorrect book ID: {book_id}, expected: {expected_book}",
                            label="incorrect_book_id",
                        )
                    ]

                library_card = call_input.get("library_card_number", "")
                expected_card = self.expected_inputs.library_card_number
                if expected_card and library_card != expected_card:
                    return [
                        EvaluationOutput(
                            score=0.0,
                            test_pass=False,
                            reason=f"Renewal used incorrect library card: {library_card}, expected: {expected_card}",
                            label="incorrect_library_card",
                        )
                    ]

                renewal_period = str(call_input.get("renewal_period", ""))
                expected_period = self.expected_inputs.renewal_period
                if expected_period and renewal_period != expected_period:
                    return [
                        EvaluationOutput(
                            score=0.0,
                            test_pass=False,
                            reason=f"Renewal used incorrect period: {renewal_period}, expected: {expected_period}",
                            label="incorrect_renewal_period",
                        )
                    ]

            return [
                EvaluationOutput(
                    score=1.0,
                    test_pass=True,
                    reason="Successfully completed book renewal with correct inputs",
                    label="renewal_successful",
                )
            ]

        except Exception as e:
            return [
                EvaluationOutput(
                    score=0.0,
                    test_pass=False,
                    reason=f"Error evaluating renewal success: {str(e)}",
                    label="evaluation_error",
                )
            ]
