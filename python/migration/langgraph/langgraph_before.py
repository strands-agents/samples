#!/usr/bin/env python3
"""
# Case Triage in LangGraph (migration starting point)

The "before" side of the [Migrate from LangGraph](https://strandsagents.com/docs/user-guide/migrate/langgraph/)
guide: a three-stage case-triage graph built with LangGraph, kept deliberately
close to the shape the guide describes so it can be compared line by line with
`strands_after.py`.

The graph has five nodes for three stages, because in a `StateGraph` a tool call
is a node the graph routes to and back from.

Each stage gets its own message window (`research_messages` and so on) through
the `messages_key` argument of `ToolNode` and `tools_condition`. The guide's
inline snippet uses one `messages` key for brevity.

    pip install langgraph langgraph-checkpoint-sqlite langchain-aws
    python langgraph_before.py [case-5501]

Needs Python 3.10 or newer and AWS credentials with Bedrock access. Set
`CASE_MODEL_ID` to pin a model.
Checkpoints go to `./cases.db` in the working directory; delete it to start a
case over.
"""

import os
import sqlite3
import sys
from typing import Annotated, TypedDict

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

MODEL_ID = os.environ.get("CASE_MODEL_ID", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")
REGION = os.environ.get("AWS_REGION", "us-east-1")

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


class CaseState(TypedDict):
    """One shared state object, as LangGraph expects."""

    research_messages: Annotated[list[AnyMessage], add_messages]
    analysis_messages: Annotated[list[AnyMessage], add_messages]
    review_messages: Annotated[list[AnyMessage], add_messages]
    case_id: str
    prompt: str
    research: str
    analysis: str
    review: str


def _model(tools: list | None = None) -> ChatBedrockConverse:
    llm = ChatBedrockConverse(model=MODEL_ID, region_name=REGION, temperature=0)
    return llm.bind_tools(tools) if tools else llm


def _stage(state: CaseState, key: str, system: str, opening: str,
           tools: list | None, field: str) -> dict:
    """Run one turn of a stage. A new call opens with a fresh human turn; a call
    that follows a ToolMessage continues the tool loop instead."""
    history = state[key]
    new_messages: list[AnyMessage] = []
    if not history or not isinstance(history[-1], ToolMessage):
        new_messages.append(HumanMessage(content=opening))
    reply = _model(tools).invoke([SystemMessage(content=system)] + history + new_messages)
    new_messages.append(reply)

    update: dict = {key: new_messages}
    if not reply.tool_calls:
        update[field] = reply.text
    return update


def research(state: CaseState) -> dict:
    return _stage(
        state, "research_messages",
        "You gather the facts of the case.",
        f"Case {state['case_id']}: {state['prompt']}",
        [fetch_case_record], "research")


def analysis(state: CaseState) -> dict:
    return _stage(
        state, "analysis_messages",
        "You weigh the options.",
        f"Facts of case {state['case_id']}:\n{state['research']}\n\n{state['prompt']}",
        [search_precedent], "analysis")


def review(state: CaseState) -> dict:
    return _stage(
        state, "review_messages",
        "You recommend a decision.",
        f"Analysis of case {state['case_id']}:\n{state['analysis']}\n\n{state['prompt']}",
        None, "review")


def _route(messages_key: str):
    """Scope tools_condition to one stage's message window."""

    def condition(state: CaseState) -> str:
        return tools_condition(state, messages_key=messages_key)

    return condition


def build_graph(db_path: str = "cases.db"):
    """Wire the five nodes and compile with a checkpointer."""
    builder = StateGraph(CaseState)
    builder.add_node("research", research)
    builder.add_node("research_tools",
                     ToolNode([fetch_case_record], messages_key="research_messages"))
    builder.add_node("analysis", analysis)
    builder.add_node("analysis_tools",
                     ToolNode([search_precedent], messages_key="analysis_messages"))
    builder.add_node("review", review)

    builder.add_edge(START, "research")
    builder.add_conditional_edges("research", _route("research_messages"),
                                  {"tools": "research_tools", END: "analysis"})
    builder.add_edge("research_tools", "research")
    builder.add_conditional_edges("analysis", _route("analysis_messages"),
                                  {"tools": "analysis_tools", END: "review"})
    builder.add_edge("analysis_tools", "analysis")
    builder.add_edge("review", END)

    conn = sqlite3.connect(db_path, check_same_thread=False)
    return builder.compile(checkpointer=SqliteSaver(conn))


# Entrypoint: callers call run_case(case_id, prompt), and that call does not
# change through the migration.
def run_case(case_id: str, prompt: str, *, db_path: str = "cases.db",
             recursion_limit: int = 25) -> dict:
    graph = build_graph(db_path)
    # External ID: case_id keys the conversation, and becomes the Strands session id.
    config = {"configurable": {"thread_id": case_id}, "recursion_limit": recursion_limit}
    return graph.invoke(
        {"research_messages": [], "analysis_messages": [], "review_messages": [],
         "case_id": case_id, "prompt": prompt,
         "research": "", "analysis": "", "review": ""},
        config,
    )


def main() -> int:
    case_id = sys.argv[1] if len(sys.argv) > 1 else "case-4127"
    prompt = (sys.argv[2] if len(sys.argv) > 2
              else "Assess the dispute and recommend a decision.")

    result = run_case(case_id, prompt)

    counts = {k.removesuffix("_messages"): len(result[k])
              for k in ("research_messages", "analysis_messages", "review_messages")}
    print(f"\nCase:     {case_id}")
    print(f"Messages: {counts}")
    print(f"\nRecommendation:\n{result['review']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
