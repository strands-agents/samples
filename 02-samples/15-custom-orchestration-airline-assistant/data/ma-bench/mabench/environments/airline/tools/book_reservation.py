"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

import json
from copy import deepcopy
from typing import Any, Dict, List
from mabench.utils import get_data
from strands import tool
from mabench.environments.airline.data import load_data



@tool

def book_reservation(
    user_id: str,
    origin: str,
    destination: str,
    flight_type: str,
    cabin: str,
    flights: List[Dict[str, Any]],
    passengers: List[Dict[str, Any]],
    payment_methods: List[Dict[str, Any]],
    total_baggages: int,
    nonfree_baggages: int,
    insurance: str,
) -> str:
    """
    Book a reservation.

    Args:
        user_id: The ID of the user to book the reservation, such as 'sara_doe_496'.
        origin: The IATA code for the origin city, such as 'SFO'.
        destination: The IATA code for the destination city, such as 'JFK'.
        flight_type: The type of flight, either 'one_way' or 'round_trip'.
        cabin: The cabin class, one of 'basic_economy', 'economy', or 'business'.
        flights: An array of objects containing details about each piece of flight.
               Each object should have 'flight_number' and 'date' properties.
        passengers: An array of objects containing details about each passenger.
                   Each object should have 'first_name', 'last_name',
                   and 'dob' properties.
        payment_methods: An array of objects containing details about each payment
                        method.
                       Each object should have 'payment_id'
                       and 'amount' properties.
        total_baggages: The total number of baggage items included in the
                        reservation.
        nonfree_baggages: The number of non-free baggage items included in the
                        reservation.
        insurance: Whether to include insurance, either 'yes' or 'no'.

    Returns:
        A JSON string representing the booked reservation or an error message.
    """
    data = load_data()
    reservations, users = data["reservations"], data["users"]
    if user_id not in users:
        return "Error: user not found"
    user = users[user_id]

    # assume each task makes at most 3 reservations
    reservation_id = "HATHAT"
    if reservation_id in reservations:
        reservation_id = "HATHAU"
        if reservation_id in reservations:
            reservation_id = "HATHAV"

    reservation = {
        "reservation_id": reservation_id,
        "user_id": user_id,
        "origin": origin,
        "destination": destination,
        "flight_type": flight_type,
        "cabin": cabin,
        "flights": deepcopy(flights),
        "passengers": passengers,
        "payment_history": payment_methods,
        "created_at": "2024-05-15T15:00:00",
        "total_baggages": total_baggages,
        "nonfree_baggages": nonfree_baggages,
        "insurance": insurance,
    }

    # update flights and calculate price
    total_price = 0
    for flight in reservation["flights"]:
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
        if flight_date_data["available_seats"][cabin] < len(passengers):
            return f"Error: not enough seats on flight {flight_number}"
        flight["price"] = flight_date_data["prices"][cabin]
        flight["origin"] = flight_data["origin"]
        flight["destination"] = flight_data["destination"]
        total_price += flight["price"] * len(passengers)

    if insurance == "yes":
        total_price += 30 * len(passengers)

    total_price += 50 * nonfree_baggages

    for payment_method in payment_methods:
        payment_id = payment_method["payment_id"]
        amount = payment_method["amount"]
        if payment_id not in user["payment_methods"]:
            return f"Error: payment method {payment_id} not found"
        if user["payment_methods"][payment_id]["source"] in [
            "gift_card",
            "certificate",
        ]:
            if user["payment_methods"][payment_id]["amount"] < amount:
                return f"Error: not enough balance in payment method {payment_id}"
    if sum(payment["amount"] for payment in payment_methods) != total_price:
        return (
            f"Error: payment amount does not add up, total price is {total_price}, "
            f"but paid {sum(payment['amount'] for payment in payment_methods)}"
        )

    # if checks pass, deduct payment and update seats
    for payment_method in payment_methods:
        payment_id = payment_method["payment_id"]
        amount = payment_method["amount"]
        if user["payment_methods"][payment_id]["source"] == "gift_card":
            user["payment_methods"][payment_id]["amount"] -= amount
        elif user["payment_methods"][payment_id]["source"] == "certificate":
            del user["payment_methods"][payment_id]

    reservations[reservation_id] = reservation
    user["reservations"].append(reservation_id)
    return json.dumps(reservation)
