"""Example tool. The agent will create more like this."""
from strands import tool


@tool
def calculator(expression: str) -> str:
    """Evaluate a Python math expression.

    Args:
        expression: A Python expression like "2 + 2 * 3".

    Returns:
        The computed result as a string.
    """
    try:
        # Restricted eval - math only
        allowed = {"__builtins__": {}}
        result = eval(expression, allowed, {})
        return str(result)
    except Exception as e:
        return f"Error: {e}"
