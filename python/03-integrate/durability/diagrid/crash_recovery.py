"""Crash a durable Strands agent mid-run, then resume it.

The agent calls three tools in order. On the first run the process exits
while step_two is running. Start the script again and Dapr resumes the
workflow: step_one is not called again, step_two runs again because it never
finished, and step_three runs for the first time. Every tool call is written
to a log file, so the script can show exactly what ran.

Run it twice with the same command:
    dapr run --app-id crash-recovery --resources-path ./resources -- uv run python crash_recovery.py

Start over with --reset.
"""

import argparse
import asyncio
import json
import os
import shutil
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Optional

from diagrid.agent.strands import DaprWorkflowAgentRunner
from strands import Agent, tool

from model import build_model
from sidecar import require_sidecar

WORKFLOW_ID = "strands-durability-demo"
STATE_DIR = Path(tempfile.gettempdir()) / "strands-durability-demo"
TOOL_LOG = STATE_DIR / "tool-calls.jsonl"
CRASH_MARKER = STATE_DIR / "crashed"
RESUME_TIMEOUT_SECONDS = 120
TOOLS = ("step_one", "step_two", "step_three")

TASK = (
    'Process the order "ORD-1042". Call step_one with the order ID, '
    "then step_two with the result of step_one, "
    "then step_three with the result of step_two."
)


def log(message: str) -> None:
    # Flush every line: the crash below exits without flushing buffers.
    print(message, flush=True)


def record(tool_name: str, event: str) -> None:
    """Append one tool event to the log file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    entry = {"tool": tool_name, "event": event, "time": time.time()}
    with TOOL_LOG.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    log(f">>> {tool_name}: {event}")


def read_log() -> list[dict]:
    if not TOOL_LOG.exists():
        return []
    return [json.loads(line) for line in TOOL_LOG.read_text().splitlines() if line]


def _count(entries: list[dict], tool_name: str, event: str) -> int:
    return Counter((e["tool"], e["event"]) for e in entries)[(tool_name, event)]


def verdict(entries: list[dict]) -> bool:
    """True when only the step that crashed ran twice."""
    return (
        _count(entries, "step_one", "start") == 1
        and _count(entries, "step_two", "start") == 2
        and _count(entries, "step_two", "done") == 1
        and _count(entries, "step_three", "start") == 1
        and _count(entries, "step_three", "done") == 1
    )


def next_action(status: Optional[str], log_exists: bool) -> str:
    """Decide what this run does: start, resume, summary or mismatch."""
    if status is None:
        return "mismatch" if log_exists else "start"
    if status.endswith(("COMPLETED", "FAILED", "TERMINATED")):
        return "summary"
    return "resume"


@tool
def step_one(order_id: str) -> str:
    """Validate the order. Always the first step.

    Args:
        order_id: The order ID to validate.
    """
    record("step_one", "start")
    record("step_one", "done")
    return f"Order {order_id} is valid. Next, call step_two with '{order_id}-validated'."


@tool
def step_two(validated_order: str) -> str:
    """Reserve stock for the validated order. Always the second step.

    Args:
        validated_order: The result of step_one.
    """
    record("step_two", "start")
    if not CRASH_MARKER.exists():
        CRASH_MARKER.touch()
        log("\n>>> Simulating a crash while step_two is running.")
        log(">>> Run the same command again to resume the workflow.\n")
        os._exit(1)
    record("step_two", "done")
    return f"Stock reserved for {validated_order}. Next, call step_three with '{validated_order}-reserved'."


@tool
def step_three(reserved_order: str) -> str:
    """Confirm the order. Always the third step.

    Args:
        reserved_order: The result of step_two.
    """
    record("step_three", "start")
    record("step_three", "done")
    return f"Order {reserved_order} is confirmed."


def print_summary(status: Optional[str]) -> int:
    entries = read_log()
    log(f"\nWorkflow status: {(status or 'unknown').split('.')[-1]}")
    log("Tool calls recorded across all runs:")
    for name in TOOLS:
        log(
            f"  {name}: started {_count(entries, name, 'start')}x, "
            f"finished {_count(entries, name, 'done')}x"
        )
    if verdict(entries):
        log("\nPASS: the workflow resumed after the crash and did not repeat completed steps.")
        return 0
    log("\nFAIL: the tool calls do not match a single crash and resume. Run with --reset to start over.")
    return 1


async def wait_for_end(runner: DaprWorkflowAgentRunner) -> Optional[str]:
    deadline = time.monotonic() + RESUME_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        status = (runner.get_workflow_status(WORKFLOW_ID) or {}).get("status")
        if next_action(status, True) != "resume":
            return status
        await asyncio.sleep(1)
    log(f"The workflow did not finish within {RESUME_TIMEOUT_SECONDS} seconds. Run with --reset to start over.")
    return None


def reset(runner: DaprWorkflowAgentRunner) -> int:
    state = runner.get_workflow_status(WORKFLOW_ID)
    if state is not None:
        if next_action(state["status"], True) == "resume":
            runner.terminate_workflow(WORKFLOW_ID)
            while next_action(runner.get_workflow_status(WORKFLOW_ID)["status"], True) == "resume":
                time.sleep(0.5)
        runner.purge_workflow(WORKFLOW_ID)
    shutil.rmtree(STATE_DIR, ignore_errors=True)
    log("Reset done. Run the script again to start a new workflow.")
    return 0


async def main(reset_requested: bool) -> int:
    require_sidecar()
    agent = Agent(
        model=build_model(),
        tools=[step_one, step_two, step_three],
        system_prompt=(
            "You process orders. Call step_one, step_two and step_three in that "
            "order, each exactly once, passing on the result of the previous step."
        ),
    )
    # The runner registers the workflow and its activities with Dapr. It must
    # start on every run, so Dapr can hand back an unfinished workflow.
    runner = DaprWorkflowAgentRunner(agent=agent, name="crash-recovery")
    log("Starting the workflow runtime. Dapr resumes an unfinished workflow right away.")
    runner.start()
    try:
        if reset_requested:
            return reset(runner)

        status = (runner.get_workflow_status(WORKFLOW_ID) or {}).get("status")
        action = next_action(status, TOOL_LOG.exists())

        if action == "mismatch":
            log(
                "The tool log and the workflow store disagree (was Redis flushed?). "
                "Run with --reset to start over."
            )
            return 1

        if action == "start":
            log(f"Starting workflow {WORKFLOW_ID}")
            async for event in runner.run_async(
                task=TASK, session_id="crash-recovery-demo", workflow_id=WORKFLOW_ID
            ):
                if event["type"] == "workflow_completed":
                    status = "COMPLETED"
                elif event["type"] in ("workflow_failed", "workflow_error"):
                    status = "FAILED"
                    log(f"Workflow did not complete: {event.get('error')}")
        elif action == "resume":
            log(f"Workflow {WORKFLOW_ID} was interrupted. Waiting for the resumed run to finish...")
            status = await wait_for_end(runner)
        else:
            log(f"Workflow {WORKFLOW_ID} already finished. Showing the earlier result.")

        return print_summary(status)
    finally:
        runner.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reset", action="store_true", help="remove the workflow and the tool log")
    raise SystemExit(asyncio.run(main(parser.parse_args().reset)))
