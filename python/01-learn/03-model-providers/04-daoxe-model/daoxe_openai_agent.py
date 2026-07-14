"""Strands agent using DaoXE via the OpenAI-compatible provider.

DaoXE base URL: https://daoxe.com/v1
Model IDs are account-scoped. DaoXE is multi-protocol; this sample uses OpenAI Chat Completions.
Not available in mainland China.
"""

from __future__ import annotations

import os
from datetime import datetime
from datetime import timezone as tz
from typing import Any
from zoneinfo import ZoneInfo

from strands import Agent, tool
from strands.models.openai import OpenAIModel


@tool
def current_time(timezone: str = "UTC") -> str:
    """Return the current time in ISO format for the given timezone."""
    if timezone.upper() == "UTC":
        timezone_obj: Any = tz.utc
    else:
        timezone_obj = ZoneInfo(timezone)
    return datetime.now(timezone_obj).isoformat()


@tool
def current_weather(city: str) -> str:
    """Return a dummy weather string for the given city (replace with a real API if needed)."""
    return f"sunny in {city}"


def main() -> None:
    api_key = os.environ.get("DAOXE_API_KEY")
    model_id = os.environ.get("DAOXE_MODEL_ID")
    if not api_key:
        raise SystemExit("Set DAOXE_API_KEY to your DaoXE API key.")
    if not model_id:
        raise SystemExit(
            "Set DAOXE_MODEL_ID to an account-scoped model ID from your DaoXE catalog "
            "(dashboard or GET https://daoxe.com/v1/models)."
        )

    model = OpenAIModel(
        client_args={
            "api_key": api_key,
            "base_url": "https://daoxe.com/v1",
        },
        model_id=model_id,
        params={
            "max_tokens": 2048,
            "temperature": 0.2,
        },
    )

    agent = Agent(
        model=model,
        system_prompt="You are a simple agent that can tell the time and the weather.",
        tools=[current_time, current_weather],
    )

    result = agent("What time is it in Seattle? And how is the weather?")
    print(result)


if __name__ == "__main__":
    main()
