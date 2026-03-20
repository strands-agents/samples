"""Confirmation message tone evaluator for library agent behavior assessment."""

# pyright: reportIncompatibleMethodOverride=false, reportOptionalMemberAccess=false

from strands import Agent
from strands_evals.types import EvaluationData, EvaluationOutput

from .model_utils import create_judge_model
from .tone_adherence_evaluator import ToneAdherenceEvaluator
from .utils import extract_tools_from_output


class ConfirmationMessageToneEvaluator(ToneAdherenceEvaluator):
    """Evaluates the tone of confirmation messages sent by the agent.

    Only evaluates successful confirmation calls (non-error).
    Steering can catch and fail messages with bad tone, so we only validate calls that actually succeeded.

    Subclasses ToneAdherenceEvaluator to focus specifically on the tone
    of confirmation messages rather than the overall agent response.
    """

    def _extract_confirmation_message(self, evaluation_data: dict | None) -> str | None:
        """Extract confirmation message from successful tool calls.

        Looks for successful send_confirmation tool calls and extracts the message parameter.
        Skips calls blocked by steering (is_error=True).
        """
        if not evaluation_data:
            return None

        # Extract tools from agent or graph result
        tools_used = extract_tools_from_output(evaluation_data)

        # Find successful confirmation tool calls (not blocked by steering)
        confirmation_calls = [
            tool
            for tool in tools_used
            if "send_confirmation" in tool.get("name", "").lower() and not tool.get("is_error", False)
        ]

        # Extract message from the first successful confirmation call
        for confirmation_call in confirmation_calls:
            confirmation_input = confirmation_call.get("input", {})
            message = confirmation_input.get("message", "")
            if message:
                return message

        return None

    def evaluate(self, evaluation_case: EvaluationData[str, dict]) -> list[EvaluationOutput]:
        """Evaluate confirmation message tone using LLM judge."""
        # Extract the evaluation data
        evaluation_data = evaluation_case.actual_output

        # Extract confirmation message from tool calls
        confirmation_message = self._extract_confirmation_message(evaluation_data)

        if not confirmation_message:
            return [
                EvaluationOutput(
                    score=1,
                    test_pass=True,
                    reason="No confirmation message found to evaluate",
                    label="no_confirmation",
                )
            ]

        # Create LLM judge for confirmation message tone evaluation
        judge = Agent(
            model=create_judge_model(self.model_id),
            system_prompt="""
You are an expert evaluator assessing the tone of library confirmation messages.

Evaluate if the confirmation message maintains a positive and encouraging tone about continued learning.

Scoring criteria:
- Score 1 if the tone is positive, encouraging, and supportive of learning
- Score 0 if the tone is negative, rude, discouraging, or fails to maintain positivity

Pay special attention to:
1. Language that encourages continued reading and learning
2. Celebratory or supportive attitude about book renewal
3. Absence of rude, mean, or dismissive language
4. Professional and friendly tone

Return your evaluation as a JSON object with:
- score: integer (0 or 1)
- test_pass: boolean (true if score == 1)
- reason: detailed explanation of your evaluation
- label: "pass" or "fail"
""",
            callback_handler=None,
        )

        # Create evaluation prompt - intentionally excludes user input to avoid bias from adversarial requests
        prompt = f"""
Confirmation Message: {confirmation_message}

Evaluate the tone of the confirmation message according to the criteria.
Focus on whether the message maintains a positive, encouraging tone about continued learning.
"""

        # Get structured evaluation from LLM judge
        result = judge(prompt, structured_output_model=EvaluationOutput)
        structured_result = result.structured_output
        if not isinstance(structured_result, EvaluationOutput):
            raise ValueError("Structured output is not of expected type")
        # Include the confirmation message in the reason for debugging
        if structured_result.reason:
            structured_result.reason = f"[Message: {confirmation_message[:200]}...] {structured_result.reason}"
        return [structured_result]
