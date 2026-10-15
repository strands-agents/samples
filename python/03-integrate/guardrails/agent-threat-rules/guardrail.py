"""Agent Threat Rules (ATR) guardrail for Strands Agents.

ATR (https://github.com/Agent-Threat-Rule/agent-threat-rules) is an open-source
(MIT) detection ruleset for AI-agent threats: prompt injection, tool-argument
tampering, context exfiltration, and malicious skill patterns. The `pyatr`
reference engine loads the bundled rules and matches input text. The whole check
runs in-process with pattern rules, so it needs no API key, no network call, and
sends no agent data off the host -- which suits regulated or data-residency
deployments where a per-turn outbound call is a non-starter.

This hook enforces at two points (both verified against the stable hooks API):
- BeforeInvocationEvent: scans the incoming user turn and cancels the invocation
  when a rule at/above `min_severity` matches.
- BeforeToolCallEvent: scans the tool arguments and cancels that tool call when a
  rule matches (e.g. an injected exfiltration URL inside tool input).

Set `shadow=True` to log matches without blocking, so a team can measure rule
hits before enforcing.
"""

from __future__ import annotations

import json
from typing import Any

from pyatr import scan
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import BeforeInvocationEvent, BeforeToolCallEvent

_SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _matches_at_or_above(text: str, min_severity: str) -> list[Any]:
    if not text:
        return []
    threshold = _SEVERITY_RANK.get(min_severity, 2)
    return [m for m in scan(text) if _SEVERITY_RANK.get(m.severity, 0) >= threshold]


def _reason(matches: list[Any]) -> str:
    ids = ", ".join(m.rule_id for m in matches[:5])
    return f"Blocked by Agent Threat Rules: {len(matches)} rule(s) matched ({ids})"


def _text_from_messages(messages: Any) -> str:
    parts: list[str] = []
    for message in messages or []:
        content = message.get("content") if isinstance(message, dict) else getattr(message, "content", None)
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            for block in content:
                text = block.get("text") if isinstance(block, dict) else getattr(block, "text", None)
                if text:
                    parts.append(text)
    return "\n".join(parts)


def _text_from_tool_use(tool_use: Any) -> str:
    if tool_use is None:
        return ""
    tool_input = tool_use.get("input") if isinstance(tool_use, dict) else getattr(tool_use, "input", None)
    if isinstance(tool_input, str):
        return tool_input
    try:
        return json.dumps(tool_input)
    except (TypeError, ValueError):
        return str(tool_input)


class ATRGuardrailHook(HookProvider):
    """Strands HookProvider that screens inputs and tool calls with ATR rules."""

    def __init__(self, *, min_severity: str = "high", shadow: bool = False) -> None:
        self.min_severity = min_severity
        self.shadow = shadow

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        registry.add_callback(BeforeInvocationEvent, self.screen_input)
        registry.add_callback(BeforeToolCallEvent, self.screen_tool_call)

    def screen_input(self, event: BeforeInvocationEvent) -> None:
        matches = _matches_at_or_above(_text_from_messages(getattr(event, "messages", None)), self.min_severity)
        if not matches:
            return
        if self.shadow:
            print(f"[ATR shadow] input would be blocked: {_reason(matches)}")
            return
        event.cancel = _reason(matches)

    def screen_tool_call(self, event: BeforeToolCallEvent) -> None:
        matches = _matches_at_or_above(_text_from_tool_use(getattr(event, "tool_use", None)), self.min_severity)
        if not matches:
            return
        if self.shadow:
            print(f"[ATR shadow] tool call would be blocked: {_reason(matches)}")
            return
        event.cancel_tool = _reason(matches)
