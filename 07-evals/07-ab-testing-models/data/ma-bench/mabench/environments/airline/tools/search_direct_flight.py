"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

import json
from mabench.utils import get_data
from strands import tool
from mabench.environments.airline.data import load_data



@tool

def search_direct_flight(origin: str, destination: str, date: str) -> str:
    """
    Search direct flights between two cities on a specific date.

    Args:
        origin: The origin city airport in three letters, such as 'JFK'.
        destination: The destination city airport in three letters, such as 'LAX'.
        date: The date of the flight in the format 'YYYY-MM-DD', such as '2024-01-01'.

    Returns:
        A JSON string containing the list of available flights.
    """
    data = load_data()
    flights = data["flights"]
    results = []
    for flight in flights.values():
        if flight["origin"] == origin and flight["destination"] == destination:
            if (
                date in flight["dates"]
                and flight["dates"][date]["status"] == "available"
            ):
                # Copy flight data except dates
                flight_info = {k: v for k, v in flight.items() if k != "dates"}
                # Update with the specific date's information
                flight_info.update(flight["dates"][date])
                # Add the date key explicitly
                flight_info["date"] = date
                results.append(flight_info)
    return json.dumps({'flights':results})
