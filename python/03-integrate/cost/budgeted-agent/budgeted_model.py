"""A Strands model wrapper that enforces a per-run dollar budget.

Strands agents decide for themselves how many model calls a task takes, so a
tool that keeps failing can turn one request into dozens of paid calls. This
wrapper sits at the model boundary -- the exact point providers bill -- and
refuses the next call once the budget for the run is spent.

It works with any Strands model provider (Bedrock, Anthropic, OpenAI, ...):
every provider reports token usage in a ``{"metadata": {"usage": ...}}``
stream event, and this wrapper prices that usage as it flows past.
"""

from __future__ import annotations

from typing import Any

from strands.models import Model


class BudgetExceededError(Exception):
    """Raised when a run's dollar budget is exhausted."""


class BudgetedModel(Model):
    """Wrap a Strands model with a hard dollar ceiling for one agent run.

    Args:
        model: The model to wrap (e.g. ``BedrockModel(...)``).
        budget_usd: Maximum spend allowed for the run, in USD.
        input_per_mtok: Price per million input tokens, in USD.
        output_per_mtok: Price per million output tokens, in USD.

    The defaults price a mid-tier model ($1.00 / $4.00 per million tokens).
    Pass your provider's actual prices for exact accounting.
    """

    def __init__(
        self,
        model: Model,
        budget_usd: float,
        input_per_mtok: float = 1.00,
        output_per_mtok: float = 4.00,
    ) -> None:
        self._model = model
        self.budget_usd = budget_usd
        self.input_per_mtok = input_per_mtok
        self.output_per_mtok = output_per_mtok
        self.spent_usd = 0.0
        self.calls = 0

    @property
    def stateful(self) -> bool:
        return self._model.stateful

    @property
    def remaining_usd(self) -> float:
        return max(0.0, self.budget_usd - self.spent_usd)

    def update_config(self, **model_config: Any) -> Any:
        return self._model.update_config(**model_config)

    def get_config(self) -> Any:
        return self._model.get_config()

    async def structured_output(self, output_model, prompt, system_prompt=None, **kwargs):
        self._check_budget()
        async for event in self._model.structured_output(output_model, prompt, system_prompt, **kwargs):
            self._account(event)
            yield event

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs):
        # The budget check runs before every model call. A runaway tool loop
        # still has to come back through the model, so it cannot slip past.
        self._check_budget()
        async for event in self._model.stream(messages, tool_specs, system_prompt, **kwargs):
            self._account(event)
            yield event

    def _check_budget(self) -> None:
        if self.spent_usd >= self.budget_usd:
            raise BudgetExceededError(
                f"budget exhausted: spent ${self.spent_usd:.4f} of "
                f"${self.budget_usd:.4f} over {self.calls} model calls"
            )

    def _account(self, event: Any) -> None:
        if not isinstance(event, dict):
            return
        usage = event.get("metadata", {}).get("usage")
        if not usage:
            return
        self.spent_usd += (
            usage.get("inputTokens", 0) / 1_000_000 * self.input_per_mtok
            + usage.get("outputTokens", 0) / 1_000_000 * self.output_per_mtok
        )
        self.calls += 1
