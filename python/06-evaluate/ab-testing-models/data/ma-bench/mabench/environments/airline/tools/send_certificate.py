"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

from mabench.utils import get_data
from strands import tool
from mabench.environments.airline.data import load_data



@tool

def send_certificate(
    user_id: str,
    amount: int,
) -> str:
    """
    Send a certificate to a user.

    Args:
        user_id: The ID of the user to book the reservation, such as 'sara_doe_496'.
        amount: Certificate amount to send.

    Returns:
        A confirmation message or an error message.
    """
    data = load_data()
    users = data["users"]
    if user_id not in users:
        return "Error: user not found"
    user = users[user_id]

    # add a certificate, assume at most 3 cases per task
    for id in [3221322, 3221323, 3221324]:
        payment_id = f"certificate_{id}"
        if payment_id not in user["payment_methods"]:
            user["payment_methods"][payment_id] = {
                "source": "certificate",
                "amount": amount,
                "id": payment_id,
            }
            msg = f"Certificate {payment_id} added to user {user_id}"
            return f"{msg} with amount {amount}."
