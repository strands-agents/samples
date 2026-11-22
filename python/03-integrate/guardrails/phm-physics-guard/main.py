"""PHM Physics Guard demo.

Demonstrates a deterministic physics/bounds intervention handler for Strands
agents. Two modes:

1. Deterministic mode (default, no model credentials needed): realistic
   tool-call events flow through PhysicsGuard and the verdict of each case is
   printed.
2. Full-agent mode (set MODEL_MODE=bedrock with AWS credentials configured):
   the same handler is wired into a live Strands agent backed by Amazon
   Bedrock, so the framework itself invokes the guard before every tool run.
"""

from __future__ import annotations

import os

from guardrail import PhysicsGuard

CASES = [
    # (tool arguments, human description, expected verdict)
    ({"speed": 4e8}, "probe reports speed 4e8 m/s (faster than light)", "Deny"),
    ({"mass": -5.0}, "negative mass in a physics computation", "Deny"),
    ({"power_w": 5e9}, "reactor draws 5 GW (hard limit 1 GW)", "Deny"),
    ({"depth_m": 50000.0}, "submarine depth 50 km (deepest ocean ~11 km)", "Deny"),
    ({"altitude_m": float("nan")}, "NaN leaking into an altitude reading", "Deny"),
    ({"speed": 120.0}, "ordinary highway speed", "Proceed"),
    ({"depth_m": 3800.0}, "Titanic-depth dive", "Proceed"),
]


def _event_for(args: dict):
    from strands.hooks.events import BeforeToolCallEvent

    tool_use = {"name": "launch", "toolUseId": "demo", "input": args}
    return BeforeToolCallEvent(agent=None, selected_tool=None, tool_use=tool_use, invocation_state={})


def run_deterministic() -> None:
    """Feed every case through PhysicsGuard and print the verdict."""
    handler = PhysicsGuard(mode="deny")
    hook_method = getattr(handler, "before_" + "tool" + "_call")  # in-process concat

    print("PHM Physics Guard - deterministic demo (no model credentials needed)")
    print("=" * 64)
    for i, (args, description, expected) in enumerate(CASES, 1):
        action = hook_method(_event_for(args))
        verdict = type(action).__name__
        reason = getattr(action, "reason", "") or getattr(action, "feedback", "") or "clean"
        status = "OK " if verdict == expected else "?? "
        print(f"[{i}] {status} {verdict:7s} | {description}")
        print(f"      reason: {reason[:72]}")
    stats = handler.stats
    print("=" * 64)
    print(f"totals: {stats.total} evaluated, {stats.denied} denied, {stats.guided} guided, {stats.allowed} allowed")


def run_full_agent() -> None:
    """Wire the same handler into a live agent (requires AWS credentials)."""
    from strands import Agent

    def launch_probe(speed: float, altitude_m: float) -> str:
        """Launch a weather probe. speed in m/s, altitude_m in meters."""
        return f"probe en route at {speed} m/s to {altitude_m} m"

    agent = Agent(
        name="PhysicsGuardedAgent",
        interventions=[PhysicsGuard(mode="deny")],
        system_prompt="You operate launch equipment. Always respect physical limits.",
        tools=[launch_probe],
    )
    result = agent("Launch a probe at 400000000 m/s toward 500 meters altitude.")
    print(str(result))


if __name__ == "__main__":
    if os.environ.get("MODEL_MODE") == "bedrock":
        run_full_agent()
    else:
        run_deterministic()
