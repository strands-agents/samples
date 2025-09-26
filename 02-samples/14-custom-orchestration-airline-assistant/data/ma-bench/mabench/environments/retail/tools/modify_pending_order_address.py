"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

import json
from mabench.utils import get_data
from strands import tool
from mabench.environments.airline.data import load_data



@tool

def modify_pending_order_address(
    order_id: str,
    address1: str,
    address2: str,
    city: str,
    state: str,
    country: str,
    zip: str,
) -> str:
    """
    Modify the shipping address of a pending order.

    The agent needs to explain the modification detail and ask for explicit user
    confirmation (yes/no) to proceed.

    Args:
        order_id: The order id, such as '#W0000000'. Be careful there is a '#'
                 symbol at the beginning of the order id.
        address1: The first line of the address, such as '123 Main St'.
        address2: The second line of the address, such as 'Apt 1' or ''.
        city: The city, such as 'San Francisco'.
        state: The province, such as 'CA'.
        country: The country, such as 'USA'.
        zip: The zip code, such as '12345'.

    Returns:
        A JSON string containing the updated order details, or an error message.
    """
    # Check if the order exists and is pending
    data = load_data()
    orders = data["orders"]
    if order_id not in orders:
        return "Error: order not found"
    order = orders[order_id]
    if order["status"] != "pending":
        return "Error: non-pending order cannot be modified"

    # Modify the address
    order["address"] = {
        "address1": address1,
        "address2": address2,
        "city": city,
        "state": state,
        "country": country,
        "zip": zip,
    }
    return json.dumps(order)
