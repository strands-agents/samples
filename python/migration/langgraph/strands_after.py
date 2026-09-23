#!/usr/bin/env python3
"""
# Case Triage in Strands (migration result)

The "after" side of the [Migrate from LangGraph](https://strandsagents.com/docs/user-guide/migrate/langgraph/)
guide: the same three-stage case triage as `langgraph_before.py`, with
the same public entrypoint and the same external ID, rebuilt on Strands.

    pip install strands-agents
    python strands_after.py [case-5501]

Needs Python 3.10 or newer and AWS credentials with Bedrock access. Set
`CASE_MODEL_ID` to pin a model.
Sessions go to `./cases/` in the working directory; delete it to start a case
over.
"""

from __future__ import annotations

import os
import sys

from strands import Agent, tool
from strands.multiagent import GraphBuilder
from strands.session import FileSessionManager

# Stand-in for the record system a real deployment would query.
CASE_RECORDS = {
    "case-4127": (
        "Case case-4127 (tenant dispute, filed 2026-03-02)\n"
        "Summary: Tenant withheld two months rent citing an unrepaired heating "
        "system. Landlord filed for possession.\n"
        "Facts on file:\n"
        "- Heating fault first reported by tenant on 2025-11-14.\n"
        "- Landlord sent a contractor on 2025-12-20, 36 days later.\n"
        "- Tenant withheld rent for January and February 2026.\n"
        "- Local code requires habitable heat within 14 days of written notice."
    ),
    "case-5501": (
        "Case case-5501 (deposit withholding, filed 2026-05-19)\n"
        "Summary: Landlord retained the full deposit for cleaning after a "
        "14-month tenancy.\n"
        "Facts on file:\n"
        "- Move-out inspection recorded normal wear on carpets.\n"
        "- No itemized deduction statement was sent within the statutory 21 days.\n"
        "- Tenant provided dated move-out photographs."
    ),
}

PRECEDENTS = [
    ("repair delay rent withholding",
     "P-118: Rent withholding upheld where the landlord exceeded the statutory "
     "repair window after written notice."),
    ("deposit itemization deadline",
     "P-204: Failure to send an itemized deduction statement within the statutory "
     "period forfeits the right to withhold."),
    ("normal wear and tear",
     "P-077: Ordinary carpet wear over a tenancy of more than twelve months is not "
     "chargeable to the tenant."),
]


@tool
def fetch_case_record(case_id: str) -> str:
    """Fetch the filed record for a case.

    Args:
        case_id: Identifier of the case to fetch
    """
    return CASE_RECORDS.get(case_id, f"No filed record exists for {case_id}.")


@tool
def search_precedent(question: str) -> str:
    """Search prior decisions for relevant precedent.

    Args:
        question: What to look for in prior decisions
    """
    words = {w.strip(".,;:?").lower() for w in question.split()}
    hits = [text for topic, text in PRECEDENTS if words & set(topic.split())]
    return "\n".join(hits or [text for _, text in PRECEDENTS])


# Entrypoint: callers call run_case(case_id, prompt) exactly as before.
def run_case(case_id: str, prompt: str, *, storage_dir: str = "./cases/",
             max_nodes: int = 10):
    # A string becomes a BedrockModel; None means the SDK default.
    model = os.environ.get("CASE_MODEL_ID")

    researcher = Agent(
        name="research",
        system_prompt="You gather the facts of the case.",
        tools=[fetch_case_record],
        model=model,
    )
    analyst = Agent(
        name="analysis",
        system_prompt="You weigh the options.",
        tools=[search_precedent],
        model=model,
    )
    reviewer = Agent(
        name="review",
        system_prompt="You recommend a decision.",
        model=model,
    )

    builder = GraphBuilder()
    builder.add_node(researcher, "research")
    builder.add_node(analyst, "analysis")
    builder.add_node(reviewer, "review")
    builder.add_edge("research", "analysis")
    builder.add_edge("analysis", "review")
    builder.set_entry_point("research")
    # Caps node executions, not the tool loop inside each agent. Without a cap
    # or a timeout the SDK logs a warning.
    builder.set_max_node_executions(max_nodes)

    # External ID: case_id is the session id, so an interrupted graph resumes
    # from it on the next call.
    builder.set_session_manager(
        FileSessionManager(session_id=case_id, storage_dir=storage_dir)
    )

    # The case id has to reach the agents, so it travels in the task text.
    return builder.build()(f"Case {case_id}: {prompt}")


def main() -> int:
    case_id = sys.argv[1] if len(sys.argv) > 1 else "case-4127"
    prompt = (sys.argv[2] if len(sys.argv) > 2
              else "Assess the dispute and recommend a decision.")

    result = run_case(case_id, prompt)

    print(f"\nCase:     {case_id}")
    print(f"Status:   {result.status}")
    print(f"Order:    {[node.node_id for node in result.execution_order]}")
    print(f"Tokens:   {result.accumulated_usage['totalTokens']}")

    review = result.results["review"].result
    print(f"\nRecommendation:\n{review}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
