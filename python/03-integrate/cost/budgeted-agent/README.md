# Per-run dollar budget for an agent

Strands agents decide for themselves how many model calls a task takes. That
is usually what you want — until a tool keeps failing and one request quietly
turns into dozens of paid calls.

This sample puts a hard dollar ceiling on a single agent run: wrap any model
in `BudgetedModel`, and the run stops the moment the budget is spent.

## How it works

`BudgetedModel` wraps the model provider, which is the exact point providers
bill:

1. **Before every model call**, it checks whether the budget is already spent
   and raises `BudgetExceededError` if so. A runaway tool loop still has to
   come back through the model for its next call, so it cannot slip past.
   (Like any model error, it reaches your code wrapped in the SDK's
   `EventLoopException`, with the budget error as `original_exception` —
   see `agent.py`.)
2. **As each response streams back**, it reads the provider-reported token
   usage (the `{"metadata": {"usage": ...}}` event every Strands provider
   emits) and prices it, so the running total is exact, not estimated.

No gateway, no proxy, no provider-specific code: it works the same with
Bedrock, Anthropic, OpenAI, or any other Strands model.

## Run it

```bash
pip install -r requirements.txt
python agent.py
```

The demo agent is told to keep retrying a lookup tool that always fails.
With a $0.05 budget you will see output like:

```
Run stopped: budget exhausted: spent $0.0512 of $0.0500 over 6 model calls
Model calls: 6
Spent: $0.0512 of $0.05 budget
```

(Exact numbers vary with the model's responses.)

## Use it in your own agent

```python
from strands import Agent
from strands.models import BedrockModel

from budgeted_model import BudgetedModel

model = BudgetedModel(
    BedrockModel(model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0"),
    budget_usd=1.00,
    input_per_mtok=3.00,   # your model's prices, USD per million tokens
    output_per_mtok=15.00,
)
agent = Agent(model=model, tools=[...])
```

One `BudgetedModel` instance is one run's budget. Create a fresh wrapper per
run, or reset `spent_usd`/`calls` between runs.

## Going further

For per-task cost accounting across many runs — receipts that break a task's
spend down step by step — see
[tokenecon](https://pypi.org/project/tokenecon/), whose Strands `CostTracker`
prices completed runs from the same usage data.
