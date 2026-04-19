"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

import json
from mabench.utils import get_data
from strands import tool
from mabench.environments.airline.data import load_data



@tool

def search_onestop_flight(origin: str, destination: str, date: str) -> str:
    """
    Search one-stop flights between two cities on a specific date.

    Args:
        origin: The origin city airport in three letters, such as 'JFK'.
        destination: The destination city airport in three letters, such as 'LAX'.
        date: The date of the flight in the format 'YYYY-MM-DD', such as '2024-05-01'.

    Returns:
        A JSON string containing the list of available one-stop flights.
    """
    data = load_data()
    flights = data["flights"]
    results = []
    for flight1 in flights.values():
        if flight1["origin"] == origin:
            for flight2 in flights.values():
                if (
                    flight2["destination"] == destination
                    and flight1["destination"] == flight2["origin"]
                ):
                    date2 = (
                        f"2024-05-{int(date[-2:])+1}"
                        if "+1" in flight1["scheduled_arrival_time_est"]
                        else date
                    )
                    if (
                        flight1["scheduled_arrival_time_est"]
                        > flight2["scheduled_departure_time_est"]
                    ):
                        continue
                    if date in flight1["dates"] and date2 in flight2["dates"]:
                        if (
                            flight1["dates"][date]["status"] == "available"
                            and flight2["dates"][date2]["status"] == "available"
                        ):
                            result1 = {k: v for k, v in flight1.items() if k != "dates"}
                            result1.update(flight1["dates"][date])
                            result1["date"] = date
                            result2 = {k: v for k, v in flight2.items() if k != "dates"}
                            result2.update(flight2["dates"][date])
                            result2["date"] = date2
                            results.append([result1, result2])
    return json.dumps({'flights':results})
