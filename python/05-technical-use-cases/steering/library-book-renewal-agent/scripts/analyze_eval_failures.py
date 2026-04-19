#!/usr/bin/env python3
import json
import sys
from collections import Counter, defaultdict


def analyze(data, name=""):
    labels = []
    by_scenario = defaultdict(list)
    for scenario in data["results"]:
        scenario_name = scenario["scenario_name"]
        for run in scenario["individual_results"]:
            for evaluator, result in run.get("details", {}).items():
                if not result.get("passed", True):
                    label = result.get("label", "unknown")
                    labels.append(label)
                    by_scenario[scenario_name].append(label)

    total = len([r for s in data["results"] for r in s["individual_results"]])
    if total == 0:
        return
    counts = Counter(labels)

    print(f"\n=== {name} ===")
    print(f"Total failed runs: {total}\n")
    print("Failure breakdown:")
    for label, count in counts.most_common():
        print(f"  {label}: {count} ({count * 100 // total}%)")

    print("\nBy scenario:")
    for scenario, scenario_labels in sorted(by_scenario.items()):
        print(f"  {scenario}:")
        for label, count in Counter(scenario_labels).most_common():
            print(f"    {label}: {count}")
    print()


with open(sys.argv[1] if len(sys.argv) > 1 else "results.json") as f:
    data = json.load(f)

ts = data["timestamp"]
for agent, results in data["aggregated_results"].items():
    failed_scenarios = []
    for scenario in results:
        if scenario.get("pass_rate", 100) < 100:
            failed_runs = [r for r in scenario["individual_results"] if not r["passed"]]
            if failed_runs:
                failed_scenarios.append(
                    {
                        "agent_version": scenario["agent_version"],
                        "scenario_name": scenario["scenario_name"],
                        "individual_results": failed_runs,
                    }
                )
    if failed_scenarios:
        outfile = f"failed-runs-{agent}.json"
        with open(outfile, "w") as f:
            json.dump({"timestamp": ts, "agent_version": agent, "results": failed_scenarios}, f, indent=2)
        print(f"Wrote {outfile}")
        analyze({"results": failed_scenarios}, agent)
