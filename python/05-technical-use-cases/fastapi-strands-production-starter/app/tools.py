"""Three local tools for the agent, defined with the Strands ``@tool`` decorator.

Mirrors the shape of the benchmark repo (three tools, one model call): the
docstring and type hints become the tool schema the model sees.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from strands import tool


@tool
def get_current_time(timezone: str) -> str:
    """Get the current time for an IANA timezone.

    Args:
        timezone: IANA timezone identifier, e.g. "America/New_York", "Europe/Paris", "UTC".

    Returns:
        A human-readable current date and time in the requested timezone.
    """
    try:
        now = datetime.now(ZoneInfo(timezone))
    except (ZoneInfoNotFoundError, ValueError):
        return f"Invalid timezone: '{timezone}'. Use an IANA identifier like 'UTC' or 'America/New_York'."
    return now.strftime("%A, %d %B %Y %H:%M:%S %Z")


@tool
def calculate(operation: str, a: float, b: float) -> str:
    """Perform a single arithmetic operation over two numbers.

    Args:
        operation: One of "add", "subtract", "multiply", "divide".
        a: The first operand.
        b: The second operand.

    Returns:
        The result as a string, or an error message for invalid input.
    """
    if operation == "add":
        return str(a + b)
    if operation == "subtract":
        return str(a - b)
    if operation == "multiply":
        return str(a * b)
    if operation == "divide":
        if b == 0:
            return "Error: cannot divide by zero."
        return str(a / b)
    return f"Unknown operation: '{operation}'. Use add, subtract, multiply, or divide."


@tool
def get_weather(latitude: float, longitude: float) -> str:
    """Get the current weather for a geographic coordinate using the open-meteo API.

    Args:
        latitude: Latitude in decimal degrees, between -90 and 90.
        longitude: Longitude in decimal degrees, between -180 and 180.

    Returns:
        A short description of the current weather, or an error message.
    """
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}&current_weather=true"
    )
    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        current = response.json().get("current_weather")
    except (httpx.HTTPError, ValueError) as exc:
        return f"Failed to reach the weather service: {exc}"
    if not current:
        return "No current weather data returned for that location."
    return (
        f"Temperature: {current['temperature']}°C, "
        f"wind speed: {current['windspeed']} km/h "
        f"(as of {current['time']})."
    )


# All local (non-MCP) tools, ready to hand to the agent.
LOCAL_TOOLS = [get_current_time, calculate, get_weather]
