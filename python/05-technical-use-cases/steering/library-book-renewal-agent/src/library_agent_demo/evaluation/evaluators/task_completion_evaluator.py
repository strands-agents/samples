"""Task completion evaluator for library agent behavior assessment."""

# pyright: reportIncompatibleMethodOverride=false, reportOptionalMemberAccess=false

from pathlib import Path

from strands import Agent
from strands_evals.evaluators import Evaluator
from strands_evals.types import EvaluationData, EvaluationOutput

from .model_utils import create_judge_model


class TaskCompletionEvaluator(Evaluator[str, dict]):
    """Evaluates whether the agent completed the user's requested task.

    Uses an LLM judge to determine if the agent:
    - Completed the specific task the user requested
    - Refused the task appropriately (e.g., policy violation)
    - Completed a different task than requested (FAIL)
    - Asked for more information (FAIL)
    """

    def __init__(self, model_id: str = "moonshotai.kimi-k2.5"):
        """Initialize the task completion evaluator.

        Args:
            model_id: The model ID to use for LLM-based evaluation
        """
        super().__init__()
        self.model_id = model_id

        # Load prompt from file
        prompt_path = Path(__file__).parent / "task_completion_prompt.script.md"
        self.system_prompt = prompt_path.read_text()

    def evaluate(self, evaluation_case: EvaluationData[str, dict]) -> list[EvaluationOutput]:
        """Evaluate task completion."""
        output = evaluation_case.actual_output
        agent_response = output.get("output", "")

        if not agent_response:
            return [
                EvaluationOutput(
                    score=0.0,
                    test_pass=False,
                    reason="No agent response found",
                    label="no_response",
                )
            ]

        # Get expected behavior from scenario
        expected_behavior = output.get("expected_behavior", "")

        # Create LLM judge for task completion evaluation
        judge = Agent(
            model=create_judge_model(self.model_id),
            system_prompt=self.system_prompt,
        )

        prompt = f"""
Expected Behavior: {expected_behavior}

Agent Response: {agent_response}

Did the agent complete the expected behavior?
"""

        # Get structured evaluation from LLM judge
        result = judge(prompt, structured_output_model=EvaluationOutput)
        structured_result = result.structured_output
        if not isinstance(structured_result, EvaluationOutput):
            raise ValueError("Structured output is not of expected type")
        return [structured_result]
