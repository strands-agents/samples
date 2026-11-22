"""PHM Physics Guard integration for Strands agents.

A deterministic, physics/bounds intervention handler: physically impossible
tool arguments (faster-than-light speeds, negative masses, probabilities above
1, NaN leaks, impossible depths) are denied *before* the tool executes.

No LLM in the loop and no external API: verdicts come from a fixed rule table
and are recomputable by anyone.
"""

from strands_phm_guard import PhysicsGuard, check_tool_args

__all__ = ["PhysicsGuard", "check_tool_args", "guard"]


def guard(args: dict) -> list[str]:
    """Evaluate raw tool arguments and return the violation list (empty = clean)."""
    return check_tool_args(args)
