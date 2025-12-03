"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

import json
from mabench.utils import get_data
from strands import tool
from mabench.environments.airline.data import load_data



@tool

def cancel_reservation(reservation_id: str) -> str:
    """
    Cancel the whole reservation.

    Args:
        reservation_id: The reservation ID, such as 'ZFA04Y'.

    Returns:
        A JSON string representing the cancelled reservation or an error message.
    """
    data = load_data()
    reservations = data["reservations"]
    if reservation_id not in reservations:
        return "Error: reservation not found"
    reservation = reservations[reservation_id]

    # reverse the payment
    refunds = []
    for payment in reservation["payment_history"]:
        refunds.append(
            {
                "payment_id": payment["payment_id"],
                "amount": -payment["amount"],
            }
        )
    reservation["payment_history"].extend(refunds)
    reservation["status"] = "cancelled"
    return json.dumps(reservation)
