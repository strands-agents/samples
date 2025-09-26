"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

from mabench.utils import get_data
from strands import tool
from mabench.environments.airline.data import load_data



@tool

def find_user_id_by_name_zip(first_name: str, last_name: str, zip: str) -> str:
    """
    Find user id by first name, last name, and zip code.

    If the user is not found, the function will return an error message. By default,
    find user id by email, and only call this function if the user is not found by
    email or cannot remember email.

    Args:
        first_name: The first name of the customer, such as 'John'.
        last_name: The last name of the customer, such as 'Doe'.
        zip: The zip code of the customer, such as '12345'.

    Returns:
        The user ID if found, or an error message if not found.
    """
    data = load_data()
    users = data["users"]
    for user_id, profile in users.items():
        if (
            profile["name"]["first_name"].lower() == first_name.lower()
            and profile["name"]["last_name"].lower() == last_name.lower()
            and profile["address"]["zip"] == zip
        ):
            return user_id
    return "Error: user not found"
