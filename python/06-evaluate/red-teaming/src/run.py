"""Attack the returns desk with GOAT, then compare the judge's verdict to the recorded tool calls.

Run: uv run src/run.py            (three full runs)
     uv run src/run.py --runs 1 --only fake_manager
"""

import argparse
import asyncio
import json
import os
import queue
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final

from strands import Agent
from strands_evals.redteam import RUN_RESULTS, GoatStrategy, RedTeamExperiment

from cases import CASES
from desk import MODEL_ID, agent_factory, bedrock_model
from tool_check import Finding, check_messages, refund_calls

DEFAULT_JUDGE_MODEL_ID: Final[str] = "us.anthropic.claude-sonnet-5-5"
DEFAULT_ATTACKER_MODEL_ID: Final[str] = "deepseek.v3.2"
JUDGE_MODEL_ID: Final[str] = os.environ.get("JUDGE_MODEL_ID", DEFAULT_JUDGE_MODEL_ID)
ATTACKER_MODEL_ID: Final[str] = os.environ.get("ATTACKER_MODEL_ID", DEFAULT_ATTACKER_MODEL_ID)
ROOT: Final[Path] = Path(__file__).resolve().parent.parent
SUITE_PATH: Final[Path] = ROOT / "suite" / "refund_desk_goat.json"


def _user_texts(messages: Sequence[Mapping[str, object]]) -> list[str]:
    texts: list[str] = []
    for message in messages:
        content = message.get("content")
        if message.get("role") != "user" or not isinstance(content, list):
            continue
        texts.extend(block["text"] for block in content if isinstance(block, dict) and "text" in block)
    return texts


def _find_agent(agents: Sequence[Agent], conversation: Sequence[Mapping[str, object]]) -> Agent | None:
    """Pair an attack's conversation with the target agent that lived through it."""
    sent = [str(turn["content"]) for turn in conversation if turn.get("role") == "attacker"]
    if not sent:
        return None
    for agent in agents:
        texts = _user_texts(agent.messages)
        if texts[: len(sent)] == sent:
            return agent
    return None


def _parse_failures(case_data: Mapping[str, object]) -> int:
    entries = case_data.get("actual_environment_state")
    if not isinstance(entries, list):
        return 0
    for entry in entries:
        if isinstance(entry, dict) and entry.get("name") == RUN_RESULTS:
            state = entry.get("state") or {}
            return int(state.get("parse_failures", 0)) if isinstance(state, dict) else 0
    return 0


def run_once(run: int, only: frozenset[str], max_turns: int, out_dir: Path) -> list[tuple[str, Finding]]:
    """Run every case once with GOAT and return the tool-check findings."""
    built: queue.SimpleQueue[Agent] = queue.SimpleQueue()

    def factory() -> Agent:
        # Message passing, not a shared list: workers hand each target back through a queue.
        agent = agent_factory()
        built.put(agent)
        return agent

    attacker = bedrock_model(ATTACKER_MODEL_ID)
    judge = bedrock_model(JUDGE_MODEL_ID)
    cases = [case for case in CASES if not only or case.name in only]
    experiment = RedTeamExperiment(
        cases=cases,
        attack_strategies=[GoatStrategy(max_turns=max_turns, model=attacker)],
        model=judge,
    )
    report = asyncio.run(experiment.run_evaluations_async(agent_factory=factory))
    out_dir.mkdir(parents=True, exist_ok=True)
    report.to_file(str(out_dir / f"report-{run}.json"))
    print(f"\n===== RUN {run} | target={MODEL_ID} attacker={ATTACKER_MODEL_ID} judge={JUDGE_MODEL_ID} =====")
    report.display()

    agents: list[Agent] = []
    while not built.empty():
        agents.append(built.get())

    failures = sum(_parse_failures(case_data) for case_data in report.cases)
    breaches = sum(1 for result in report.attack_results() if result.state == "breached")
    print(f"judge breaches: {breaches} | attacker parse failures: {failures}")

    findings: list[tuple[str, Finding]] = []
    evidence: list[dict[str, object]] = []
    print("tool-check:")
    for result in report.attack_results():
        name = str(result.case_name).split("__")[0]
        agent = _find_agent(agents, result.conversation)
        messages = list(agent.messages) if agent is not None else []
        case_findings = check_messages(messages)
        for finding in case_findings:
            findings.append((name, finding))
            print(f"  VIOLATION run={run} case={name} kind={finding.violation} {finding.detail}")
        kinds = ",".join(f.violation for f in case_findings) or "none"
        calls = refund_calls(messages)
        print(
            f"  {name:<18} judge={result.state:<9} score={result.score:.2f}  "
            f"issue_refund calls={len(calls)}  tool-check={kinds}"
        )
        for call in calls:
            print(f"    issue_refund({call})")
        evidence.append(
            {
                "case": name,
                "judge_state": result.state,
                "judge_score": result.score,
                "judge_reason": result.reason,
                "tool_check": [{"kind": f.violation, "detail": f.detail} for f in case_findings],
                "issue_refund_calls": calls,
                "conversation": result.conversation,
                "target_messages": messages,
            }
        )
    (out_dir / f"run-{run}.json").write_text(json.dumps(evidence, indent=2, default=str))
    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--only", action="append", default=[], help="case name; repeatable")
    parser.add_argument("--max-turns", type=int, default=10)
    parser.add_argument("--out", type=Path, default=ROOT / "runs")
    args = parser.parse_args()

    SUITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    RedTeamExperiment(
        cases=list(CASES),
        attack_strategies=[GoatStrategy(max_turns=args.max_turns, model=bedrock_model(ATTACKER_MODEL_ID))],
        model=bedrock_model(JUDGE_MODEL_ID),
    ).to_file(str(SUITE_PATH))
    totals: dict[str, int] = {}
    for run in range(1, args.runs + 1):
        for _, finding in run_once(run, frozenset(args.only), args.max_turns, args.out):
            totals[finding.violation] = totals.get(finding.violation, 0) + 1
    print(f"\ntool-check totals across {args.runs} run(s): {totals or 'no violations'}")


if __name__ == "__main__":
    main()
