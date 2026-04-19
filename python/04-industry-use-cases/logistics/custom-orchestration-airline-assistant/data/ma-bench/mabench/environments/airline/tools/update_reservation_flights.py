"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

import json
from copy import deepcopy
from typing import List, Dict, Any
from mabench.utils import get_data
from strands import tool
from mabench.environments.airline.data import load_data



@tool

def update_reservation_flights(
    reservation_id: str,
    cabin: str,
    flights: List[Dict[str, Any]],
    payment_id: str,
) -> str:
    """
    Update the flight information of a reservation.

    Args:
        reservation_id: The reservation ID, such as 'ZFA04Y'.
        cabin: The cabin class, one of 'basic_economy', 'economy', or 'business'.
        flights: An array of objects containing details about each piece of flight in
                the ENTIRE new reservation. Even if a flight segment is not changed,
                it should still be included in the array. Each object should have
                'flight_number' and 'date' properties.
        payment_id: The payment id stored in user profile, such as
                    'credit_card_7815826',
                   'gift_card_7815826',
                   'certificate_7815826'.

    Returns:
        A JSON string representing the updated reservation or an error message.
    """
    data = load_data()
    users, reservations = data["users"], data["reservations"]
    if reservation_id not in reservations:
        return "Error: reservation not found"
    reservation = reservations[reservation_id]

    # update flights and calculate price
    total_price = 0
    flights = deepcopy(flights)
    for flight in flights:
        # if existing flight, ignore
        if _ := [
            f
            for f in reservation["flights"]
            if f["flight_number"] == flight["flight_number"]
            and f["date"] == flight["date"]
            and cabin == reservation["cabin"]
        ]:
            total_price += _[0]["price"] * len(reservation["passengers"])
            flight["price"] = _[0]["price"]
            flight["origin"] = _[0]["origin"]
            flight["destination"] = _[0]["destination"]
            continue
        flight_number = flight["flight_number"]
        if flight_number not in data["flights"]:
            return f"Error: flight {flight_number} not found"
        flight_data = data["flights"][flight_number]
        if flight["date"] not in flight_data["dates"]:
            return f"Error: flight {flight_number} not found on date {flight['date']}"
        flight_date_data = flight_data["dates"][flight["date"]]
        if flight_date_data["status"] != "available":
            return (
                f"Error: flight {flight_number} not available on date {flight['date']}"
            )
        if flight_date_data["available_seats"][cabin] < len(reservation["passengers"]):
            return f"Error: not enough seats on flight {flight_number}"
        flight["price"] = flight_date_data["prices"][cabin]
        flight["origin"] = flight_data["origin"]
        flight["destination"] = flight_data["destination"]
        total_price += flight["price"] * len(reservation["passengers"])

    total_price -= sum(flight["price"] for flight in reservation["flights"]) * len(
        reservation["passengers"]
    )

    # check payment
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

    # if checks pass, deduct payment and update seats
    if payment_method["source"] == "gift_card":
        payment_method["amount"] -= total_price
    reservation["flights"] = flights
    if total_price != 0:
        reservation["payment_history"].append(
            {
                "payment_id": payment_id,
                "amount": total_price,
            }
        )
    # do not make flight database update here, assume it takes time to be updated
    return json.dumps(reservation)
