"""Demo: an agent with a flaky tool, stopped by a $0.05 budget.

The agent is told to keep retrying a lookup tool that always fails. Without a
budget it would keep paying for model calls until the SDK's own limits stop
it. Wrapped in ``BudgetedModel``, the run halts the moment the $0.05 ceiling
is crossed, with an exact account of what was spent.

Run:
    pip install -r requirements.txt
    python agent.py
"""

from strands import Agent, tool
from strands.models import BedrockModel
from strands.types.exceptions import EventLoopException

from budgeted_model import BudgetExceededError, BudgetedModel


@tool
def flaky_lookup(query: str) -> str:
    """Look up a record in the internal vendor service."""
    # Simulated flaky service: it never succeeds, so the agent keeps retrying.
    return "ERROR: vendor service unavailable (503). Please retry the lookup."


def main() -> None:
    model = BudgetedModel(
        BedrockModel(model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0"),
        budget_usd=0.05,
        # Claude Sonnet prices, USD per million tokens.
        input_per_mtok=3.00,
        output_per_mtok=15.00,
    )
    agent = Agent(model=model, tools=[flaky_lookup], callback_handler=None)

    try:
        agent("Use flaky_lookup to find the Q3 vendor record. Keep retrying until it succeeds.")
        print("Run finished on its own (the tool eventually behaved).")
    except EventLoopException as exc:
        # The SDK wraps model errors in EventLoopException; the budget error
        # is the original exception inside it.
        if isinstance(exc.original_exception, BudgetExceededError):
            print(f"Run stopped: {exc.original_exception}")
        else:
            raise

    print(f"Model calls: {model.calls}")
    print(f"Spent: ${model.spent_usd:.4f} of ${model.budget_usd:.2f} budget")


if __name__ == "__main__":
    main()
