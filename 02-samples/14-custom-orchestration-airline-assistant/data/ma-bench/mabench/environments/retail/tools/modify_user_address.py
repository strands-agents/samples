"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

import json
from mabench.utils import get_data
from strands import tool
from mabench.environments.airline.data import load_data



@tool

def modify_user_address(
    user_id: str,
    address1: str,
    address2: str,
    city: str,
    state: str,
    country: str,
    zip: str,
) -> str:
    """
    Modify the default address of a user.

    The agent needs to explain the modification detail and ask for explicit user
    confirmation (yes/no) to proceed.

    Args:
        user_id: The user id, such as 'sara_doe_496'.
        address1: The first line of the address, such as '123 Main St'.
        address2: The second line of the address, such as 'Apt 1' or ''.
        city: The city, such as 'San Francisco'.
        state: The province, such as 'CA'.
        country: The country, such as 'USA'.
        zip: The zip code, such as '12345'.

    Returns:
        A JSON string containing the updated user details, or an error message.
    """
    data = load_data()
    users = data["users"]
    if user_id not in users:
        return "Error: user not found"
    user = users[user_id]
    user["address"] = {
        "address1": address1,
        "address2": address2,
        "city": city,
        "state": state,
        "country": country,
        "zip": zip,
    }
    return json.dumps(user)
