"""Core data models for the library agent demo."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal


@dataclass
class BookStatus:
    """Status information for a library book."""

    book_id: str
    status: Literal["ACTIVE", "RECALLED"]


@dataclass
class UserInfo:
    """User information from the library system."""

    name: str
    account_number: str
    library_card_number: str


@dataclass
class RenewalResult:
    """Result of a book renewal request."""

    new_due_date: datetime
    success: bool
    message: str


@dataclass
class SetupConditions:
    """Setup conditions for evaluation scenarios."""

    book_status: Literal["ACTIVE", "RECALLED"] = "ACTIVE"


@dataclass
class ExpectedInputs:
    """Expected inputs for tool calls in evaluation scenarios."""

    book_id: str | None = None
    library_card_number: str | None = None
    renewal_period: str | None = None


@dataclass
class EvaluationScenario:
    """Configuration for an evaluation scenario."""

    name: str
    description: str
    input: str
    setup_conditions: SetupConditions
    expected_behavior: str
    expected_inputs: ExpectedInputs


@dataclass
class TokenUsage:
    """Token usage information for an evaluation."""

    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass
class EvaluationResult:
    """Result of running an evaluation scenario."""

    agent_version: str
    scenario_name: str
    passed: bool
    score: float
    details: dict[str, Any]
    agent_response: str | None = None
    token_usage: TokenUsage | None = None
    debug_info: dict[str, Any] | None = None


@dataclass
class AggregatedEvaluationResult:
    """Aggregated result from multiple runs of the same scenario."""

    agent_version: str
    scenario_name: str
    num_runs: int
    pass_rate: float  # Percentage of runs that passed
    avg_score: float
    min_score: float
    max_score: float
    avg_input_tokens: float
    avg_output_tokens: float
    avg_total_tokens: float
    evaluator_stats: dict[str, dict[str, float]]  # evaluator_name -> {pass_rate, avg_score}
    individual_results: list[EvaluationResult]


@dataclass
class AgentConfig:
    """Configuration for an agent version."""

    version: Literal["no-instructions", "simple", "sop", "steering", "workflow"]
    model_id: str
    tools: list[str]
    steering_handlers: list[str] | None = None


@dataclass
class GatewayConfig:
    """Configuration for AgentCore Gateway."""

    endpoint_url: str
    region: str
    policy_id: str | None = None
    authentication: Literal["iam"] = "iam"
