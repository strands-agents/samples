"""Run a Strands agent as a durable Dapr workflow.

Each model call and each tool call becomes a workflow activity, so Dapr
records the progress of the run step by step.

Run with:
    dapr run --app-id simple-agent --resources-path ./resources -- uv run python simple_agent.py
"""

import asyncio

from diagrid.agent.strands import DaprWorkflowAgentRunner
from strands import Agent, tool

from model import build_model
from sidecar import require_sidecar


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city.

    Args:
        city: The name of the city.
    """
    return f"The weather in {city} is cloudy with light rain, 12 degrees Celsius."


@tool
def convert_temperature(celsius: float) -> str:
    """Convert a temperature from Celsius to Fahrenheit.

    Args:
        celsius: The temperature in degrees Celsius.
    """
    fahrenheit = celsius * 9 / 5 + 32
    return f"{celsius} degrees Celsius is {fahrenheit:.1f} degrees Fahrenheit."


async def main() -> None:
    require_sidecar()
    agent = Agent(
        model=build_model(),
        tools=[get_weather, convert_temperature],
        system_prompt="You are a helpful weather assistant. Use your tools to answer.",
    )
    runner = DaprWorkflowAgentRunner(agent=agent, name="simple-agent")

    runner.start()
    try:
        async for event in runner.run_async(
            task="What's the weather in Amsterdam, and what is that in Fahrenheit?",
            session_id="simple-agent-demo",
        ):
            kind = event["type"]
            if kind == "workflow_started":
                print(f"Workflow started: {event['workflow_id']}")
            elif kind == "workflow_status_changed":
                print(f"Status: {event['status'].split('.')[-1]}")
            elif kind == "workflow_completed":
                print("\nTool calls:")
                for call in event.get("tool_calls", []):
                    print(f"  - {call['tool_name']}")
                print(f"\nAnswer:\n{event.get('result', '')}")
            elif kind in ("workflow_failed", "workflow_error"):
                print(f"Workflow did not complete: {event.get('error')}")
    finally:
        runner.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
