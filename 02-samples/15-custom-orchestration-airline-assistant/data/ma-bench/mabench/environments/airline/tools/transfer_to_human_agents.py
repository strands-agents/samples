"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""



from strands import tool
from mabench.environments.airline.data import load_data
@tool

def transfer_to_human_agents(summary: str) -> str:
    """
    Transfer the user to a human agent, with a summary of the user's issue.
    Only transfer if the user explicitly asks for a human agent, or if the user's
    issue cannot be resolved by the agent with the available tools.

    Args:
        summary: A summary of the user's issue.

    Returns:
        A confirmation message that the transfer was successful.
    """
    return "Transfer successful"
