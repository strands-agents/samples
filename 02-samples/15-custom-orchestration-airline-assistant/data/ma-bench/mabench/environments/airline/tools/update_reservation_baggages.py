"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

import json
from mabench.utils import get_data
from strands import tool
from mabench.environments.airline.data import load_data



@tool

def update_reservation_baggages(
    reservation_id: str,
    total_baggages: int,
    nonfree_baggages: int,
    payment_id: str,
) -> str:
    """
    Update the baggage information of a reservation.

    Args:
        reservation_id: The reservation ID, such as 'ZFA04Y'.
        total_baggages: The updated total number of baggage items included in the
                        reservation.
        nonfree_baggages: The updated number of non-free baggage items included
                         in the reservation.
        payment_id: The payment id stored in user profile, such as
                   'credit_card_7815826', 'gift_card_7815826', or
                   'certificate_7815826'.

    Returns:
        A JSON string representing the updated reservation or an error message.
    """
    data = load_data()
    users, reservations = data["users"], data["reservations"]
    if reservation_id not in reservations:
        return "Error: reservation not found"
    reservation = reservations[reservation_id]

    total_price = 50 * max(0, nonfree_baggages - reservation["nonfree_baggages"])
    if payment_id not in users[reservation["user_id"]]["payment_methods"]:
        return "Error: payment method not found"
    payment_method = users[reservation["user_id"]]["payment_methods"][payment_id]
    if payment_method["source"] == "certificate":
        return "Error: certificate cannot be used to update reservation"
    elif (
        payment_method["source"] == "gift_card"
        and payment_method["amount"] < total_price
    ):
        return "Error: gift card balance is not enough"

    reservation["total_baggages"] = total_baggages
    reservation["nonfree_baggages"] = nonfree_baggages
    if payment_method["source"] == "gift_card":
        payment_method["amount"] -= total_price

    if total_price != 0:
        reservation["payment_history"].append(
            {
                "payment_id": payment_id,
                "amount": total_price,
            }
        )

    return json.dumps(reservation)
