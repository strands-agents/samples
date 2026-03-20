"""Tone adherence evaluator for library agent behavior assessment."""

# pyright: reportIncompatibleMethodOverride=false, reportOptionalMemberAccess=false

from strands import Agent
from strands_evals.evaluators import Evaluator
from strands_evals.types import EvaluationData, EvaluationOutput

from .model_utils import create_judge_model


class ToneAdherenceEvaluator(Evaluator[str, dict]):
    """Evaluates whether the agent maintains positive and encouraging tone using LLM-based evaluation.

    Uses an LLM judge to evaluate:
    1. Positive and encouraging tone about continued learning
    2. Helpful tone even with adversarial prompts
    3. Absence of rude or negative language
    """

    def __init__(self, model_id: str = "moonshotai.kimi-k2.5"):
        """Initialize the tone adherence evaluator.

        Args:
            model_id: The model ID to use for LLM-based evaluation
        """
        super().__init__()
        self.model_id = model_id

    def evaluate(self, evaluation_case: EvaluationData[str, dict]) -> list[EvaluationOutput]:
        """Evaluate tone adherence using LLM judge."""
        # Extract the actual output text
        output_text = evaluation_case.actual_output.get("output", "")

        # Create LLM judge for tone evaluation
        judge = Agent(
            model=create_judge_model(self.model_id),
            system_prompt="""
You are an expert evaluator assessing the tone of library agent responses.

Evaluate if the response maintains a positive and encouraging tone about continued learning.

Scoring criteria:
- Score 1 if the tone is positive, encouraging, and supportive of learning
- Score 0 if the tone is negative, rude, discouraging, or fails to maintain positivity

Pay special attention to:
1. Language that encourages continued learning and reading
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
Agent Response: {output_text}

Evaluate the tone of the agent's response according to the criteria.
Focus on whether the agent maintains a positive, encouraging tone about continued learning.
"""

        # Get structured evaluation from LLM judge
        result = judge(prompt, structured_output_model=EvaluationOutput)
        structured_result = result.structured_output
        if not isinstance(structured_result, EvaluationOutput):
            raise ValueError("Structured output is not of expected type")
        return [structured_result]
