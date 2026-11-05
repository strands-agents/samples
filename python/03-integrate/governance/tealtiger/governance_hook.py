"""
TealTiger Governance Hook for Strands Agents.

A HookProvider that intercepts tool calls via BeforeToolCallEvent and applies
deterministic governance: policy evaluation, cost tracking, PII detection,
and kill switch — all without an LLM in the governance path.

Reference implementation: https://github.com/agentguard-ai/tealtiger
"""

from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry


@dataclass
class GovernanceDecision:
    """Structured decision record for every tool call evaluation."""

    decision_id: str
    tool: str
    action: Literal["allow", "deny"]
    reason: str
    correlation_id: str
    evaluation_time_ms: float
    risk_score: int = 0
    triggered_policies: list[str] = field(default_factory=list)
    pii_detected: list[str] = field(default_factory=list)


PII_PATTERNS: dict[str, re.Pattern] = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "phone": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
}


class TealTigerGovernanceHook(HookProvider):
    """Deterministic governance hook for Strands Agents.

    Intercepts every tool call via BeforeToolCallEvent and evaluates against
    configured policies. Denied calls are cancelled via event.cancel_tool.

    Args:
        mode: "observe" (log only), "monitor" (log warnings), "enforce" (block)
        policies: List of policy dicts defining governance rules
        budget: Optional session budget in USD
        agent_id: Optional agent identifier for audit trail
    """

    def __init__(
        self,
        mode: Literal["observe", "monitor", "enforce"] = "observe",
        policies: list[dict[str, Any]] | None = None,
        budget: float | None = None,
        agent_id: str | None = None,
    ) -> None:
        self.mode = mode
        self.policies = policies or []
        self.budget = budget
        self.agent_id = agent_id or f"strands-agent-{uuid.uuid4().hex[:8]}"
        self._session_cost: float = 0.0
        self._frozen: bool = False
        self._audit_trail: list[GovernanceDecision] = []

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        """Register the governance evaluation on BeforeToolCallEvent."""
        registry.add_callback(BeforeToolCallEvent, self.evaluate_tool_call)

    def evaluate_tool_call(self, event: BeforeToolCallEvent) -> None:
        """Evaluate a tool call against governance policies."""
        start = time.perf_counter()
        correlation_id = uuid.uuid4().hex[:8]
        tool_name = event.tool_use["name"]
        tool_input = event.tool_use.get("input", {})
        tool_input_str = json.dumps(tool_input) if isinstance(tool_input, dict) else str(tool_input)

        triggered: list[str] = []
        pii_found: list[str] = []
        action: Literal["allow", "deny"] = "allow"
        reason = "Compliant with all policies"
        risk_score = 0

        # Kill switch
        if self._frozen:
            action = "deny"
            reason = f"Agent {self.agent_id} is frozen (kill switch active)"
            risk_score = 100
            triggered.append("kill_switch")
        else:
            for policy in self.policies:
                policy_type = policy.get("type", "")

                if policy_type == "tool_allowlist":
                    allowed = policy.get("allowed", [])
                    if tool_name not in allowed:
                        action = "deny"
                        reason = f"Tool '{tool_name}' not in allowlist: {allowed}"
                        risk_score = max(risk_score, 80)
                        triggered.append(f"tool_allowlist:{tool_name}")

                elif policy_type == "tool_blocklist":
                    blocked = policy.get("blocked", [])
                    if tool_name in blocked:
                        action = "deny"
                        reason = f"Tool '{tool_name}' is explicitly blocked"
                        risk_score = max(risk_score, 90)
                        triggered.append(f"tool_blocklist:{tool_name}")

                elif policy_type == "pii_block":
                    categories = policy.get("categories", list(PII_PATTERNS.keys()))
                    for cat in categories:
                        pattern = PII_PATTERNS.get(cat)
                        if pattern and pattern.search(tool_input_str):
                            pii_found.append(cat)
                            action = "deny"
                            reason = f"PII detected in tool args: {cat}"
                            risk_score = max(risk_score, 95)
                            triggered.append(f"pii_block:{cat}")

                elif policy_type == "cost_limit":
                    max_cost = policy.get("max_per_session", float("inf"))
                    if self._session_cost >= max_cost:
                        action = "deny"
                        reason = f"Session budget exhausted: ${self._session_cost:.2f} >= ${max_cost:.2f}"
                        risk_score = max(risk_score, 70)
                        triggered.append("cost_limit")

        elapsed_ms = (time.perf_counter() - start) * 1000

        decision = GovernanceDecision(
            decision_id=f"gd-{uuid.uuid4().hex[:12]}",
            tool=tool_name,
            action=action,
            reason=reason,
            correlation_id=correlation_id,
            evaluation_time_ms=elapsed_ms,
            risk_score=risk_score,
            triggered_policies=triggered,
            pii_detected=pii_found,
        )
        self._audit_trail.append(decision)

        # Enforce
        if action == "deny" and self.mode == "enforce":
            event.cancel_tool = reason
        elif action == "deny" and self.mode == "monitor":
            print(f"[TealTiger MONITOR] DENY {tool_name}: {reason}")

        status = "ALLOWED" if action == "allow" else "DENIED "
        print(f"[TealTiger] {status} | {tool_name} | {elapsed_ms:.2f}ms | {correlation_id}")

    def freeze(self) -> None:
        """Activate kill switch — block all subsequent tool calls."""
        self._frozen = True
        print(f"[TealTiger] FROZEN: Agent {self.agent_id}")

    def unfreeze(self) -> None:
        """Deactivate kill switch — resume normal operation."""
        self._frozen = False
        print(f"[TealTiger] UNFROZEN: Agent {self.agent_id}")

    def record_cost(self, amount_usd: float) -> None:
        """Record cost for budget tracking."""
        self._session_cost += amount_usd

    def report(self) -> dict[str, Any]:
        """Return session governance summary."""
        return {
            "agent_id": self.agent_id,
            "mode": self.mode,
            "total_evaluations": len(self._audit_trail),
            "allowed": sum(1 for d in self._audit_trail if d.action == "allow"),
            "denied": sum(1 for d in self._audit_trail if d.action == "deny"),
            "total_cost_usd": self._session_cost,
            "budget_usd": self.budget,
        }

    @property
    def audit_trail(self) -> list[GovernanceDecision]:
        """Access the full audit trail."""
        return self._audit_trail
