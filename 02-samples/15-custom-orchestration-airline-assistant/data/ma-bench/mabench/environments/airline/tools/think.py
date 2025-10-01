"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""



from strands import tool
from mabench.environments.airline.data import load_data
@tool

def think(thought: str) -> str:
    """
    Use this function to think about something.

    It will not obtain new information or change the database, but just append
    the thought to the log. Use it when complex reasoning is needed.

    Args:
        thought: A thought to think about.

    Returns:
        An empty string.
    """
    return ""
