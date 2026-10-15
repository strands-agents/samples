"""A 10-case Strands Evals regression suite for the agent.

Runs the same agent the service uses (local tools, no MCP required) against ten
cases spanning each tool and general Q&A, and scores the responses with the
LLM-based ``OutputEvaluator``. Cases that exercise a tool also declare an
``expected_trajectory`` so a ``TrajectoryEvaluator`` can check tool selection.

Run it:

    python -m evals.eval_suite

Requires AWS credentials with Bedrock access (the default judge model), plus
whatever the agent's own provider needs. Results print to the console and are
saved to ``fastapi_starter_evaluation.json``.
"""

from __future__ import annotations

from strands import Agent
from strands.models import BedrockModel
from strands_evals import Case, Experiment, eval_task
from strands_evals.evaluators import OutputEvaluator, TrajectoryEvaluator

from app.tools import LOCAL_TOOLS

SYSTEM_PROMPT = (
    "You are a helpful, concise assistant. You have tools to tell the time, do "
    "arithmetic, and look up the weather. Use a tool only when it genuinely helps."
)


@eval_task()
def build_agent_for_eval() -> Agent:
    """Return a fresh agent for each case (auto-invoked with ``case.input``)."""
    return Agent(
        model=BedrockModel(),
        tools=LOCAL_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        callback_handler=None,
    )


CASES: list[Case] = [
    Case[str, str](
        name="time-utc",
        input="What time is it right now in UTC?",
        expected_output="A current date and time in the UTC timezone.",
        expected_trajectory=["get_current_time"],
        metadata={"category": "time"},
    ),
    Case[str, str](
        name="time-tokyo",
        input="Tell me the current time in Tokyo.",
        expected_output="A current date and time in the Asia/Tokyo timezone.",
        expected_trajectory=["get_current_time"],
        metadata={"category": "time"},
    ),
    Case[str, str](
        name="math-add",
        input="What is 128 plus 256?",
        expected_output="384",
        expected_trajectory=["calculate"],
        metadata={"category": "math"},
    ),
    Case[str, str](
        name="math-divide",
        input="Divide 144 by 12.",
        expected_output="12",
        expected_trajectory=["calculate"],
        metadata={"category": "math"},
    ),
    Case[str, str](
        name="math-divide-by-zero",
        input="What is 10 divided by 0?",
        expected_output="An explanation that division by zero is not possible.",
        expected_trajectory=["calculate"],
        metadata={"category": "math"},
    ),
    Case[str, str](
        name="weather-london",
        input="What's the current weather at latitude 51.5, longitude -0.12?",
        expected_output="A short description of the current weather including temperature.",
        expected_trajectory=["get_weather"],
        metadata={"category": "weather"},
    ),
    Case[str, str](
        name="weather-paris",
        input="Give me the current weather for latitude 48.85 and longitude 2.35.",
        expected_output="A short description of the current weather including temperature.",
        expected_trajectory=["get_weather"],
        metadata={"category": "weather"},
    ),
    Case[str, str](
        name="knowledge-capital",
        input="What is the capital of France?",
        expected_output="The capital of France is Paris.",
        metadata={"category": "knowledge"},
    ),
    Case[str, str](
        name="reasoning-widgets",
        input=(
            "If it takes 5 machines 5 minutes to make 5 widgets, how long does it take "
            "100 machines to make 100 widgets?"
        ),
        expected_output="5 minutes",
        metadata={"category": "reasoning"},
    ),
    Case[str, str](
        name="no-tool-greeting",
        input="Hello! Can you briefly say what you can help with?",
        expected_output="A brief, friendly overview of the assistant's capabilities, without calling a tool.",
        metadata={"category": "general"},
    ),
]


def main() -> None:
    """Run the 10-case regression suite and print + save the report."""
    output_evaluator = OutputEvaluator(
        rubric=(
            "Evaluate the response on: (1) accuracy — is it factually correct and "
            "consistent with the expected output; (2) completeness — does it fully "
            "answer; (3) clarity. Score 1.0 when all are met, 0.5 when partially met, "
            "0.0 when inadequate."
        ),
        include_inputs=True,
    )
    trajectory_evaluator = TrajectoryEvaluator(
        rubric=(
            "Pass if the tools the agent called match the expected trajectory for the "
            "task: time questions should call get_current_time, arithmetic should call "
            "calculate, and weather should call get_weather. Score 1.0 for the right "
            "tool(s), lower when tools are missing, extra, or wrong."
        ),
    )

    experiment = Experiment[str, str](
        cases=CASES,
        evaluators=[output_evaluator, trajectory_evaluator],
    )
    report = experiment.run_evaluations(build_agent_for_eval)

    print("=== FastAPI + Strands starter — regression suite ===")
    report.run_display()
    experiment.to_file("fastapi_starter_evaluation")
    print("\nSaved to ./fastapi_starter_evaluation.json")


if __name__ == "__main__":
    main()
