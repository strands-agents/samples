"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

import json
from typing import List
from mabench.utils import get_data
from strands import tool
from mabench.environments.airline.data import load_data



@tool

def return_delivered_order_items(
    order_id: str, item_ids: List[str], payment_method_id: str
) -> str:
    """
    Return some items of a delivered order.

    The order status will be changed to 'return requested'. The agent needs to explain
    the return detail and ask for explicit user confirmation (yes/no) to proceed.
    The user will receive follow-up email for how and where to return the item.

    Args:
        order_id: The order id, such as '#W0000000'. Be careful there is a '#' symbol
                 at the beginning of the order id.
        item_ids: The item ids to be returned, each such as '1008292230'. There could
                 be duplicate items in the list.
        payment_method_id: The payment method id to pay or receive refund for the item
                          price difference, such as 'gift_card_0000000' or
                          'credit_card_0000000'. These can be looked up from the user
                          or order details.

    Returns:
        A JSON string containing the updated order details, or an error message.
    """
    data = load_data()
    orders = data["orders"]

    # Check if the order exists and is delivered
    if order_id not in orders:
        return "Error: order not found"
    order = orders[order_id]
    if order["status"] != "delivered":
        return "Error: non-delivered order cannot be returned"

    # Check if the payment method exists and is either the original payment method or a gift card
    user_payment_methods = data["users"][order["user_id"]]["payment_methods"]
    if payment_method_id not in user_payment_methods:
        return "Error: payment method not found"
    if (
        "gift_card" not in payment_method_id
        and payment_method_id != order["payment_history"][0]["payment_method_id"]
    ):
        return (
            "Error: payment method should be either the original payment method"
            " or a gift card"
        )

    # Check if the items to be returned exist
    # (there could be duplicate items in either list)
    all_item_ids = [item["item_id"] for item in order["items"]]
    for item_id in item_ids:
        if item_ids.count(item_id) > all_item_ids.count(item_id):
            return "Error: some item not found"

    # Update the order status
    order["status"] = "return requested"
    order["return_items"] = sorted(item_ids)
    order["return_payment_method_id"] = payment_method_id

    return json.dumps(order)
