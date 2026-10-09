"""OpenAI variant of the 10-case regression suite (run it without AWS).

Identical cases and rubrics to ``eval_suite.py``, but both the agent under test
and the judge run on OpenAI (``OpenAIModel``) instead of Bedrock, so it runs
with only an ``OPENAI_API_KEY`` — handy when Bedrock credentials aren't
available. The shipped default remains ``eval_suite.py`` (Bedrock).

Run it:

    python -m evals.eval_suite_openai
"""

from __future__ import annotations

from strands import Agent
from strands.models.openai import OpenAIModel
from strands_evals import Experiment, eval_task
from strands_evals.evaluators import OutputEvaluator, TrajectoryEvaluator

from app.config import get_settings
from app.tools import LOCAL_TOOLS

# Reuse the exact cases and prompt from the shipped suite.
from evals.eval_suite import CASES, SYSTEM_PROMPT


def _openai_model() -> OpenAIModel:
    settings = get_settings()
    return OpenAIModel(
        client_args={"api_key": settings.openai_api_key},
        model_id=settings.openai_model_id,
    )


@eval_task()
def build_agent_for_eval() -> Agent:
    """Return a fresh OpenAI-backed agent for each case."""
    return Agent(
        model=_openai_model(),
        tools=LOCAL_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        callback_handler=None,
    )


def main() -> None:
    """Run the 10-case regression suite with OpenAI as agent and judge."""
    judge = _openai_model()

    output_evaluator = OutputEvaluator(
        rubric=(
            "Evaluate the response on: (1) accuracy — is it factually correct and "
            "consistent with the expected output; (2) completeness — does it fully "
            "answer; (3) clarity. Score 1.0 when all are met, 0.5 when partially met, "
            "0.0 when inadequate."
        ),
        model=judge,
        include_inputs=True,
    )
    trajectory_evaluator = TrajectoryEvaluator(
        rubric=(
            "Pass if the tools the agent called match the expected trajectory for the "
            "task: time questions should call get_current_time, arithmetic should call "
            "calculate, and weather should call get_weather. Score 1.0 for the right "
            "tool(s), lower when tools are missing, extra, or wrong."
        ),
        model=judge,
    )

    experiment = Experiment[str, str](
        cases=CASES,
        evaluators=[output_evaluator, trajectory_evaluator],
    )
    report = experiment.run_evaluations(build_agent_for_eval)

    print("=== FastAPI + Strands starter — regression suite (OpenAI) ===")
    report.run_display()
    experiment.to_file("fastapi_starter_evaluation_openai")
    print("\nSaved to ./fastapi_starter_evaluation_openai.json")


if __name__ == "__main__":
    main()
