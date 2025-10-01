"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

import json
from strands import tool
from mabench.environments.airline.data import load_data



@tool

def list_all_airports() -> str:
    """
    List all airports and their cities.

    Args:
        None

    Returns:
        A JSON string mapping airport codes to city names.
    """
    airports = [
        "SFO",
        "JFK",
        "LAX",
        "ORD",
        "DFW",
        "DEN",
        "SEA",
        "ATL",
        "MIA",
        "BOS",
        "PHX",
        "IAH",
        "LAS",
        "MCO",
        "EWR",
        "CLT",
        "MSP",
        "DTW",
        "PHL",
        "LGA",
    ]
    cities = [
        "San Francisco",
        "New York",
        "Los Angeles",
        "Chicago",
        "Dallas",
        "Denver",
        "Seattle",
        "Atlanta",
        "Miami",
        "Boston",
        "Phoenix",
        "Houston",
        "Las Vegas",
        "Orlando",
        "Newark",
        "Charlotte",
        "Minneapolis",
        "Detroit",
        "Philadelphia",
        "LaGuardia",
    ]
    return json.dumps({airport: city for airport, city in zip(airports, cities)})
