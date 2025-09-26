"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

from mabench.utils import get_data
from strands import tool
from mabench.environments.airline.data import load_data



@tool

def find_user_id_by_email(email: str) -> str:
    """
    Find user id by email. If the user is not found, the function will return an error
    message.

    Args:
        email: The email of the user, such as 'something@example.com'.

    Returns:
        The user ID if found, or an error message if not found.
    """
    data = load_data()
    users = data["users"]
    for user_id, profile in users.items():
        if profile["email"].lower() == email.lower():
            return user_id
    return "Error: user not found"
