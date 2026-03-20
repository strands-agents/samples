"""Main CLI application for the library agent demo."""

import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table
from rich.text import Text

from .config import ensure_output_directory, get_log_level
from .evaluation.runner import (
    LibraryAgentEvaluationRunner,
    generate_comprehensive_report,
    print_comparative_summary,
    print_comprehensive_report,
    run_comprehensive_evaluation_suite,
)
from .evaluation.scenarios import ALL_SCENARIOS
from .models import AggregatedEvaluationResult, EvaluationResult, EvaluationScenario

# Set up logging with configuration
log_level = getattr(logging, get_log_level(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

console = Console()
logger = logging.getLogger(__name__)


def get_agent_by_version(agent_version: str):
    """Get agent instance by version name."""
    if agent_version == "no-instructions":
        from .agents.no_instructions_agent import NoInstructionsAgent

        return NoInstructionsAgent()
    elif agent_version == "simple":
        from .agents.simple_instruction_agent import SimpleInstructionAgent

        return SimpleInstructionAgent()
    elif agent_version == "sop":
        from .agents.sop_agent import SOPAgent

        return SOPAgent()
    elif agent_version == "steering":
        from .agents.steering_agent import SteeringAgent

        return SteeringAgent()

    elif agent_version == "workflow":
        from .agents.workflow_agent import WorkflowAgent

        return WorkflowAgent()
    else:
        raise ValueError(f"Unknown agent version: {agent_version}")


def get_scenario_by_name(scenario_name: str):
    """Get scenario by name."""
    scenario_map = {scenario.name: scenario for scenario in ALL_SCENARIOS}

    # Handle CLI-friendly names
    name_mapping = {
        "happy-path": "happy_path",
        "recalled": "recalled_book",
        "mismatched-card": "mismatched_card",
        "excessive-period": "excessive_period",
        "adversarial-tone": "adversarial_tone",
        "informational-query": "informational_query",
    }

    actual_name = name_mapping.get(scenario_name, scenario_name)

    if actual_name not in scenario_map:
        raise ValueError(f"Unknown scenario: {scenario_name}")

    return scenario_map[actual_name]


def run_interactive_mode(agent_version: str) -> None:
    """Run agent in interactive mode for book renewal requests."""
    console.print(f"\n[bold green]Interactive Library Agent ({agent_version})[/bold green]")
    console.print("Type 'quit' or 'exit' to stop\n")

    try:
        agent = get_agent_by_version(agent_version)

        while True:
            try:
                user_input = input("User: ").strip()

                if user_input.lower() in ["quit", "exit", "q", "/quit", "/exit"]:
                    console.print("[yellow]Goodbye![/yellow]")
                    break

                if not user_input:
                    continue

                console.print("[blue]Processing request...[/blue]")
                result = agent.process_request(user_input)

                if isinstance(result, dict) and "output" in result:
                    response = result["output"]
                else:
                    response = str(result)

                console.print(f"\n\n[green]Agent:[/green] {response}\n")

            except KeyboardInterrupt:
                console.print("\n[yellow]Goodbye![/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}\n")

    except Exception as e:
        console.print(f"[red]Failed to initialize agent:[/red] {e}")


def display_evaluation_table(result: Any) -> None:
    """Display detailed evaluation results in a table."""
    if result.details:
        console.print("\nEvaluator Details:")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Evaluator", width=30)
        table.add_column("Status", width=9)
        table.add_column("Score", width=7)
        table.add_column("Reason", width=80)

        for evaluator_name, details in result.details.items():
            if isinstance(details, dict):
                eval_status = "✅ PASS" if details.get("passed", False) else "❌ FAIL"
                eval_score = f"{details.get('score', 0.0):.2f}"
                reason = details.get("reason", "")
                table.add_row(evaluator_name, eval_status, eval_score, reason)

        console.print(table)


def print_run_result(result: Any, prefix: str = "") -> None:
    """Print a single evaluation run result with details."""
    status = "✅ PASS" if result.passed else "❌ FAIL"
    token_info = ""
    if result.token_usage:
        token_info = f" | Tokens: {result.token_usage.input_tokens}→{result.token_usage.output_tokens}"
    console.print(f"{prefix}{status} Score: {result.score:.2f}{token_info}")
    display_evaluation_table(result)


MAX_RETRIES = 3


def run_scenario_with_retry(
    runner: LibraryAgentEvaluationRunner,
    agent_version: str,
    scenario: EvaluationScenario,
) -> EvaluationResult:
    """Run a scenario with retry on failure."""
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            agent = get_agent_by_version(agent_version)
            return runner.run_scenario(agent, scenario)
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
    raise last_error  # type: ignore[misc]


def run_single_evaluation_task(task: tuple[str, EvaluationScenario, int]) -> tuple[str, str, int, EvaluationResult]:
    """Run a single evaluation task. Returns (agent_version, scenario_name, iteration, result)."""
    agent_version, scenario, iteration = task
    runner = LibraryAgentEvaluationRunner()
    result = run_scenario_with_retry(runner, agent_version, scenario)
    return (agent_version, scenario.name, iteration, result)


def aggregate_evaluation_results(all_results: dict[str, list]) -> dict[str, list]:
    """Aggregate multiple runs of the same scenario into averaged results."""
    from collections import defaultdict

    aggregated = {}
    runner = LibraryAgentEvaluationRunner()

    for agent_version, results in all_results.items():
        # Group results by scenario
        scenario_groups = defaultdict(list)
        for result in results:
            scenario_groups[result.scenario_name].append(result)

        # Aggregate each scenario group
        agent_aggregated = []
        for _scenario_name, scenario_results in scenario_groups.items():
            agg_result = runner.aggregate_results(scenario_results)
            agent_aggregated.append(agg_result)

        aggregated[agent_version] = agent_aggregated

    return aggregated


def print_aggregated_summary(aggregated_results: dict[str, list]) -> None:
    """Print summary of aggregated results."""
    console.print("\n[bold]Aggregated Results Summary:[/bold]")

    for agent_version, results in aggregated_results.items():
        total_scenarios = len(results)
        avg_pass_rate = sum(r.pass_rate for r in results) / total_scenarios if results else 0
        avg_score = sum(r.avg_score for r in results) / total_scenarios if results else 0

        console.print(f"\n{agent_version}:")
        console.print(f"  Scenarios: {total_scenarios}")
        console.print(f"  Average Pass Rate: {avg_pass_rate:.1f}%")
        console.print(f"  Average Score: {avg_score:.2f}")


def print_aggregated_comparative_summary(aggregated_results: dict[str, list]) -> None:
    """Print comparative summary of aggregated results."""
    console.print("\n" + "=" * 100)
    console.print("AGGREGATED COMPARATIVE EVALUATION SUMMARY")
    console.print("=" * 100)

    # Print summary for each agent
    for agent_version, results in aggregated_results.items():
        console.print(f"\nAgent: {agent_version}")
        console.print("-" * 100)

        if not results:
            console.print("  No results available")
            continue

        total_scenarios = len(results)
        avg_pass_rate = sum(r.pass_rate for r in results) / total_scenarios
        avg_score = sum(r.avg_score for r in results) / total_scenarios
        avg_input = sum(r.avg_input_tokens for r in results) / total_scenarios
        avg_output = sum(r.avg_output_tokens for r in results) / total_scenarios

        console.print(f"  Scenarios: {total_scenarios}")
        console.print(f"  Average Pass Rate: {avg_pass_rate:.1f}%")
        console.print(f"  Average Score: {avg_score:.2f}")
        console.print(f"  Average Tokens: {avg_input:.0f} input, {avg_output:.0f} output")

    # Print scenario-by-scenario comparison
    console.print("\n" + "=" * 100)
    console.print("SCENARIO-BY-SCENARIO COMPARISON (AVERAGED)")
    console.print("=" * 100)

    # Get all scenario names
    all_scenario_names = set()
    for results in aggregated_results.values():
        all_scenario_names.update(r.scenario_name for r in results)

    # Print comparison for each scenario
    for scenario_name in sorted(all_scenario_names):
        console.print(f"\n{scenario_name}:")
        console.print("-" * 50)

        for agent_version, results in aggregated_results.items():
            # Find result for this scenario
            scenario_result = next((r for r in results if r.scenario_name == scenario_name), None)

            if scenario_result:
                console.print(
                    f"  {agent_version:<20} Pass Rate: {scenario_result.pass_rate:>5.1f}%  "
                    f"Avg Score: {scenario_result.avg_score:.2f}  "
                    f"Tokens: {scenario_result.avg_input_tokens:.0f}→{scenario_result.avg_output_tokens:.0f}"
                )
            else:
                console.print(f"  {agent_version:<20} ⚠️  NO RESULT")

    # Print overall agent summary
    console.print("\n" + "=" * 100)
    console.print("OVERALL AGENT SUMMARY")
    console.print("=" * 100)
    console.print(f"{'Agent':<20} {'Pass Rate':>10} {'Input Tokens':>14} {'Output Tokens':>15}")
    console.print("-" * 60)
    for agent_version, results in aggregated_results.items():
        if results:
            n = len(results)
            avg_pass = sum(r.pass_rate for r in results) / n
            avg_in = sum(r.avg_input_tokens for r in results) / n
            avg_out = sum(r.avg_output_tokens for r in results) / n
            console.print(f"{agent_version:<20} {avg_pass:>9.1f}% {avg_in:>14,.0f} {avg_out:>15,.0f}")

    console.print("=" * 100)


def print_aggregated_detailed_report(aggregated_results: dict[str, list]) -> None:
    """Print detailed report of aggregated results."""
    console.print("\n" + "=" * 100)
    console.print("DETAILED AGGREGATED EVALUATION REPORT")
    console.print("=" * 100)

    for agent_version, results in aggregated_results.items():
        console.print(f"\n[bold]Agent: {agent_version}[/bold]")
        console.print("=" * 100)

        for result in results:
            console.print(f"\n[bold cyan]{result.scenario_name}[/bold cyan]")
            console.print(f"  Runs: {result.num_runs}")
            console.print(f"  Pass Rate: {result.pass_rate:.1f}%")
            console.print(
                f"  Avg Score: {result.avg_score:.2f} (min: {result.min_score:.2f}, max: {result.max_score:.2f})"
            )
            console.print(f"  Avg Input Tokens: {result.avg_input_tokens:.0f}")
            console.print(f"  Avg Output Tokens: {result.avg_output_tokens:.0f}")
            console.print(f"  Avg Total Tokens: {result.avg_total_tokens:.0f}")

            # Show per-evaluator statistics
            if result.evaluator_stats:
                console.print("\n  [bold]Evaluator Statistics:[/bold]")
                for evaluator_name, stats in result.evaluator_stats.items():
                    console.print(
                        f"    {evaluator_name}: "
                        f"Pass Rate: {stats['pass_rate']:.1f}%, "
                        f"Avg Score: {stats['avg_score']:.2f}"
                    )


def save_single_evaluation_results(
    agent_version: str, scenario_name: str, results: list[EvaluationResult], agg: AggregatedEvaluationResult
) -> None:
    """Save single evaluation results to results.json."""
    output_data = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "agent_version": agent_version,
            "scenario_name": scenario_name,
            "num_iterations": len(results),
        },
        "aggregate": {
            "pass_rate": agg.pass_rate,
            "avg_score": agg.avg_score,
            "min_score": agg.min_score,
            "max_score": agg.max_score,
            "avg_input_tokens": agg.avg_input_tokens,
            "avg_output_tokens": agg.avg_output_tokens,
            "avg_total_tokens": agg.avg_total_tokens,
        },
        "iterations": [
            {
                "iteration": i + 1,
                "passed": r.passed,
                "score": r.score,
                "details": r.details,
                "token_usage": {
                    "input_tokens": r.token_usage.input_tokens,
                    "output_tokens": r.token_usage.output_tokens,
                    "total_tokens": r.token_usage.total_tokens,
                }
                if r.token_usage
                else None,
            }
            for i, r in enumerate(results)
        ],
    }
    with open("results.json", "w") as f:
        json.dump(output_data, f, indent=2)
    console.print("\n[green]✓[/green] Results saved to: results.json")


def save_aggregated_results_to_file(aggregated_results: dict[str, list], output_file: str) -> None:
    """Save aggregated results to JSON file."""
    from dataclasses import asdict

    # Convert to serializable format
    serializable_results = {}
    for agent_version, results in aggregated_results.items():
        serializable_results[agent_version] = [
            {**asdict(r), "individual_results": [asdict(ir) for ir in r.individual_results]} for r in results
        ]

    output_data = {
        "timestamp": datetime.now().isoformat(),
        "aggregated_results": serializable_results,
    }

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2, default=str)

    console.print(f"\n[green]✓[/green] Results saved to: {output_file}")


def save_summary_to_file(aggregated_results: dict[str, list], output_file: str, completed: int, failed: int) -> None:
    """Save summary report to markdown file."""
    lines = [
        f"Completed: {completed} successful, {failed} failed",
        "",
        "=" * 100,
        "AGGREGATED COMPARATIVE EVALUATION SUMMARY",
        "=" * 100,
        "",
    ]

    for agent_version, results in aggregated_results.items():
        if results:
            n = len(results)
            avg_pass = sum(r.pass_rate for r in results) / n
            avg_score = sum(r.avg_score for r in results) / n
            avg_in = sum(r.avg_input_tokens for r in results) / n
            avg_out = sum(r.avg_output_tokens for r in results) / n
            lines.extend(
                [
                    f"Agent: {agent_version}",
                    "-" * 100,
                    f"  Scenarios: {n}",
                    f"  Average Pass Rate: {avg_pass:.1f}%",
                    f"  Average Score: {avg_score:.2f}",
                    f"  Average Tokens: {avg_in:.0f} input, {avg_out:.0f} output",
                    "",
                ]
            )

    lines.extend(["=" * 100, "SCENARIO-BY-SCENARIO COMPARISON (AVERAGED)", "=" * 100, ""])

    all_scenario_names = set()
    for results in aggregated_results.values():
        all_scenario_names.update(r.scenario_name for r in results)

    for scenario_name in sorted(all_scenario_names):
        lines.extend([f"{scenario_name}:", "-" * 50])
        for agent_version, results in aggregated_results.items():
            scenario_result = next((r for r in results if r.scenario_name == scenario_name), None)
            if scenario_result:
                lines.append(
                    f"  {agent_version:<20} Pass Rate: {scenario_result.pass_rate:>5.1f}%  "
                    f"Avg Score: {scenario_result.avg_score:.2f}  "
                    f"Tokens: {scenario_result.avg_input_tokens:.0f}→{scenario_result.avg_output_tokens:.0f}"
                )
        lines.append("")

    lines.extend(["=" * 100, "OVERALL AGENT SUMMARY", "=" * 100])
    lines.append(f"{'Agent':<20} {'Pass Rate':>10} {'Input Tokens':>14} {'Output Tokens':>15}")
    lines.append("-" * 60)
    for agent_version, results in aggregated_results.items():
        if results:
            n = len(results)
            avg_pass = sum(r.pass_rate for r in results) / n
            avg_in = sum(r.avg_input_tokens for r in results) / n
            avg_out = sum(r.avg_output_tokens for r in results) / n
            lines.append(f"{agent_version:<20} {avg_pass:>9.1f}% {avg_in:>14,.0f} {avg_out:>15,.0f}")
    lines.append("=" * 100)

    with open(output_file, "w") as f:
        f.write("\n".join(lines))

    console.print(f"[green]✓[/green] Summary saved to: {output_file}")


def run_single_evaluation(agent_version: str, scenario_name: str, num_iterations: int = 1) -> None:
    """Run a single evaluation scenario."""
    console.print("\n[bold blue]Running Evaluation[/bold blue]")
    console.print(f"Agent: {agent_version}")
    console.print(f"Scenario: {scenario_name}")
    if num_iterations > 1:
        console.print(f"Iterations: {num_iterations}")
    console.print()

    try:
        scenario = get_scenario_by_name(scenario_name)
        runner = LibraryAgentEvaluationRunner()

        if num_iterations == 1:
            result = run_scenario_with_retry(runner, agent_version, scenario)

            status = "[green]✅ PASS[/green]" if result.passed else "[red]❌ FAIL[/red]"
            console.print(f"Result: {status}")
            console.print(f"Score: {result.score:.2f}")

            if result.token_usage:
                console.print(
                    f"Token Usage: {result.token_usage.input_tokens} → "
                    f"{result.token_usage.output_tokens} ({result.token_usage.total_tokens} total)"
                )

            if result.details:
                console.print("\n[bold]Evaluator Details:[/bold]")
                display_evaluation_table(result)
        else:
            results = []
            for i in range(num_iterations):
                console.print(f"Running iteration {i + 1}/{num_iterations}...")
                result = run_scenario_with_retry(runner, agent_version, scenario)
                results.append(result)
                status = "[green]✅ PASS[/green]" if result.passed else "[red]❌ FAIL[/red]"
                console.print(f"Result: {status}, Score: {result.score:.2f}")
                display_evaluation_table(result)

            agg = runner.aggregate_results(results)
            status = "[green]✅ PASS[/green]" if agg.pass_rate == 100.0 else "[red]❌ FAIL[/red]"
            console.print("\n[bold]Aggregate Results:[/bold]")
            console.print(f"Result: {status}")
            console.print(f"Pass Rate: {agg.pass_rate:.1f}%")
            console.print(f"Avg Score: {agg.avg_score:.2f} (min: {agg.min_score:.2f}, max: {agg.max_score:.2f})")
            console.print(
                f"Avg Tokens: {agg.avg_input_tokens:.0f} → "
                f"{agg.avg_output_tokens:.0f} ({agg.avg_total_tokens:.0f} total)"
            )

            # Save results to results.json
            save_single_evaluation_results(agent_version, scenario_name, results, agg)

    except Exception as e:
        console.print(f"[red]Error running evaluation:[/red] {e}")


def run_agent_evaluation(agent_version: str, num_iterations: int = 1) -> None:
    """Run all scenarios for a specific agent."""
    console.print(f"\n[bold blue]Running All Scenarios for {agent_version.upper()} Agent[/bold blue]")
    if num_iterations > 1:
        console.print(f"Running {num_iterations} iterations per scenario\n")
    else:
        console.print()

    try:
        runner = LibraryAgentEvaluationRunner()

        if num_iterations == 1:
            results = []
            for scenario in ALL_SCENARIOS:
                console.print(f"Running scenario: [cyan]{scenario.name}[/cyan]")
                result = run_scenario_with_retry(runner, agent_version, scenario)
                results.append(result)
                print_run_result(result, prefix="  ")
                console.print()

            console.print(f"\n[bold]Summary for {agent_version.upper()} Agent:[/bold]")
            passed_count = sum(1 for r in results if r.passed)
            avg_score = sum(r.score for r in results) / len(results)
            total_input_tokens = sum(r.token_usage.input_tokens for r in results if r.token_usage)
            total_output_tokens = sum(r.token_usage.output_tokens for r in results if r.token_usage)
            total_tokens = sum(r.token_usage.total_tokens for r in results if r.token_usage)

            console.print(f"Passed: {passed_count}/{len(results)}")
            console.print(f"Average Score: {avg_score:.2f}")
            console.print(f"Total Tokens: {total_input_tokens}→{total_output_tokens} ({total_tokens})")
        else:
            aggregated_results = []
            for scenario in ALL_SCENARIOS:
                console.print(f"Running scenario: [cyan]{scenario.name}[/cyan] ({num_iterations} iterations)")
                scenario_results = []
                for i in range(num_iterations):
                    result = run_scenario_with_retry(runner, agent_version, scenario)
                    scenario_results.append(result)
                    console.print(f"  [bold]Run {i + 1}:[/bold]")
                    print_run_result(result, prefix="    ")

                agg = runner.aggregate_results(scenario_results)
                aggregated_results.append(agg)

                status = "✅ PASS" if agg.pass_rate == 100.0 else "❌ FAIL"
                console.print(
                    f"  [bold]Summary:[/bold] {status} Pass Rate: {agg.pass_rate:.1f}% | Avg Score: {agg.avg_score:.2f}"
                )
                console.print()

            console.print(f"\n[bold]Summary for {agent_version.upper()} Agent:[/bold]")
            full_pass_count = sum(1 for a in aggregated_results if a.pass_rate == 100.0)
            avg_pass_rate = sum(a.pass_rate for a in aggregated_results) / len(aggregated_results)
            avg_score = sum(a.avg_score for a in aggregated_results) / len(aggregated_results)

            console.print(f"Scenarios with 100% Pass Rate: {full_pass_count}/{len(aggregated_results)}")
            console.print(f"Average Pass Rate: {avg_pass_rate:.1f}%")
            console.print(f"Average Score: {avg_score:.2f}")

            console.print(f"Scenarios with 100% Pass Rate: {full_pass_count}/{len(aggregated_results)}")
            console.print(f"Average Pass Rate: {avg_pass_rate:.1f}%")
            console.print(f"Average Score: {avg_score:.2f}")

    except Exception as e:
        console.print(f"[red]Error running agent evaluation:[/red] {e}")


def run_scenario_evaluation(scenario_name: str, num_iterations: int = 1) -> None:
    """Run a specific scenario across all agents."""
    console.print(f"\n[bold blue]Running {scenario_name.upper()} Scenario Across All Agents[/bold blue]")
    if num_iterations > 1:
        console.print(f"Running {num_iterations} iterations per agent\n")
    else:
        console.print()

    try:
        scenario = get_scenario_by_name(scenario_name)
        runner = LibraryAgentEvaluationRunner()
        agent_versions = ["no-instructions", "simple", "sop", "steering", "workflow"]

        if num_iterations == 1:
            results = []
            for agent_version in agent_versions:
                console.print(f"Testing [cyan]{agent_version}[/cyan] agent")
                result = run_scenario_with_retry(runner, agent_version, scenario)
                results.append(result)
                print_run_result(result, prefix="  ")
                console.print()

            console.print(f"[bold]Summary for {scenario_name.upper()} Scenario:[/bold]")
            passed_count = sum(1 for r in results if r.passed)
            avg_score = sum(r.score for r in results) / len(results)
            console.print(f"Agents Passed: {passed_count}/{len(results)}")
            console.print(f"Average Score: {avg_score:.2f}")
        else:
            aggregated_results = []
            for agent_version in agent_versions:
                console.print(f"Testing [cyan]{agent_version}[/cyan] agent ({num_iterations} iterations)")
                agent_results = []
                for i in range(num_iterations):
                    result = run_scenario_with_retry(runner, agent_version, scenario)
                    agent_results.append(result)
                    console.print(f"  [bold]Run {i + 1}:[/bold]")
                    print_run_result(result, prefix="    ")

                agg = runner.aggregate_results(agent_results)
                aggregated_results.append(agg)

                status = "✅ PASS" if agg.pass_rate == 100.0 else "❌ FAIL"
                console.print(
                    f"  [bold]Summary:[/bold] {status} Pass Rate: {agg.pass_rate:.1f}% | Avg Score: {agg.avg_score:.2f}"
                )
                console.print()

            console.print(f"[bold]Summary for {scenario_name.upper()} Scenario:[/bold]")
            full_pass_count = sum(1 for a in aggregated_results if a.pass_rate == 100.0)
            avg_pass_rate = sum(a.pass_rate for a in aggregated_results) / len(aggregated_results)
            avg_score = sum(a.avg_score for a in aggregated_results) / len(aggregated_results)

            console.print(f"Agents with 100% Pass Rate: {full_pass_count}/{len(aggregated_results)}")
            console.print(f"Average Pass Rate: {avg_pass_rate:.1f}%")
            console.print(f"Average Score: {avg_score:.2f}")

    except Exception as e:
        console.print(f"[red]Error running scenario evaluation:[/red] {e}")


def save_results_to_file(results: dict[str, Any], output_file: str) -> None:
    """Save evaluation results to a JSON file."""
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_file) if os.path.dirname(output_file) else "."
        os.makedirs(output_dir, exist_ok=True)

        # Convert results to JSON-serializable format
        json_results = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_agents": len(results),
                "total_scenarios": len(ALL_SCENARIOS) if results else 0,
                "total_evaluations": sum(len(agent_results) for agent_results in results.values()),
            },
            "results": {},
        }

        for agent_version, agent_results in results.items():
            json_results["results"][agent_version] = []
            for result in agent_results:
                result_dict = {
                    "agent_version": result.agent_version,
                    "scenario_name": result.scenario_name,
                    "passed": result.passed,
                    "score": result.score,
                    "details": result.details,
                }

                # Add token usage if available
                if result.token_usage:
                    result_dict["token_usage"] = {
                        "input_tokens": result.token_usage.input_tokens,
                        "output_tokens": result.token_usage.output_tokens,
                        "total_tokens": result.token_usage.total_tokens,
                    }

                json_results["results"][agent_version].append(result_dict)

        with open(output_file, "w") as f:
            json.dump(json_results, f, indent=2)

        console.print(f"[green]Results saved to {output_file}[/green]")

    except Exception as e:
        console.print(f"[red]Error saving results:[/red] {e}")
        logger.error(f"Failed to save results to {output_file}: {e}")


def display_welcome_message() -> None:
    """Display welcome message with system information."""
    welcome_text = Text()
    welcome_text.append("Library Agent Control Demo\n", style="bold blue")
    welcome_text.append(
        "Demonstrating different approaches to controlling AI agent behavior",
        style="italic",
    )

    panel = Panel(welcome_text, title="Welcome", border_style="blue")
    console.print(panel)


def handle_cli_error(error: Exception, context: str) -> None:
    """Handle CLI errors with consistent formatting."""
    console.print(f"[red]Error in {context}:[/red] {error}")
    logger.error(f"CLI error in {context}: {error}", exc_info=True)

    # Provide helpful suggestions based on error type
    if "No module named" in str(error):
        console.print("[yellow]Hint:[/yellow] Try running 'uv sync --all-extras --dev' to install dependencies")
    elif "Permission denied" in str(error):
        console.print("[yellow]Hint:[/yellow] Check file permissions or try running with appropriate privileges")
    elif "Connection" in str(error) or "timeout" in str(error).lower():
        console.print("[yellow]Hint:[/yellow] Check your network connection and AWS credentials")


def validate_environment() -> bool:
    """Validate that the environment is properly configured."""
    try:
        # Basic validation - just check that we can access environment
        get_log_level()
        return True

    except Exception as e:
        console.print(f"[red]Environment validation failed:[/red] {e}")
        return False


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
def cli(verbose: bool, quiet: bool):
    """Library Agent Control Demo CLI - Demonstrating different approaches to controlling AI agent behavior."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif quiet:
        logging.getLogger().setLevel(logging.ERROR)

    # Validate environment on startup
    if not validate_environment():
        console.print("[yellow]Warning:[/yellow] Environment validation failed. Some features may not work correctly.")


@cli.command()
def status():
    """Show system status and configuration information."""
    try:
        display_welcome_message()

        # System information
        console.print("\n[bold]System Information:[/bold]")
        info_table = Table(show_header=False, box=None)
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="white")

        info_table.add_row("Python Version", f"{sys.version.split()[0]}")
        info_table.add_row("Log Level", get_log_level())
        bedrock_profile = os.getenv("BEDROCK_PROFILE")
        if bedrock_profile:
            info_table.add_row("Bedrock Profile", bedrock_profile)

        console.print(info_table)

        # Available agents and scenarios
        console.print("\n[bold]Available Components:[/bold]")
        console.print("Agent Versions: 5 (no-instructions, simple, sop, steering, workflow)")
        console.print(f"Evaluation Scenarios: {len(ALL_SCENARIOS)}")
        console.print(f"Total Possible Evaluations: {5 * len(ALL_SCENARIOS)}")

        # Check dependencies
        console.print("\n[bold]Dependency Check:[/bold]")
        try:
            import strands  # noqa: F401

            console.print("✅ Strands SDK available")
        except ImportError:
            console.print("❌ Strands SDK not available")

        try:
            import boto3  # noqa: F401

            console.print("✅ AWS SDK (boto3) available")
        except ImportError:
            console.print("❌ AWS SDK (boto3) not available")

        try:
            from mcp.client.streamable_http import streamablehttp_client  # noqa: F401

            console.print("✅ MCP client available")
        except ImportError:
            console.print("❌ MCP client not available")

    except Exception as e:
        handle_cli_error(e, "status check")


@cli.command()
@click.option(
    "--agent-version",
    type=click.Choice(["no-instructions", "simple", "sop", "steering", "workflow"]),
    default="no-instructions",
    help="Agent version to run interactively",
)
def interactive(agent_version: str) -> None:
    """Run agent in interactive mode for book renewal requests."""
    try:
        run_interactive_mode(agent_version)
    except Exception as e:
        handle_cli_error(e, "interactive mode")


@cli.command()
@click.option(
    "--agent-version",
    type=click.Choice(["no-instructions", "simple", "sop", "steering", "workflow"]),
    required=True,
    help="Agent version to evaluate",
)
@click.option(
    "--scenario",
    type=click.Choice(
        [
            "happy-path",
            "recalled",
            "mismatched-card",
            "excessive-period",
            "adversarial-tone",
            "informational-query",
        ]
    ),
    required=True,
    help="Evaluation scenario to run",
)
@click.option(
    "-n",
    "--num-iterations",
    type=int,
    default=1,
    help="Number of times to run the scenario (for calculating averages)",
)
def evaluate(agent_version: str, scenario: str, num_iterations: int) -> None:
    """Run a single evaluation scenario against a specific agent."""
    try:
        run_single_evaluation(agent_version, scenario, num_iterations)
    except Exception as e:
        handle_cli_error(e, f"evaluation of {agent_version} agent with {scenario} scenario")


@cli.command()
@click.option(
    "--agent-version",
    type=click.Choice(["no-instructions", "simple", "sop", "steering", "workflow"]),
    required=True,
    help="Agent version to evaluate against all scenarios",
)
@click.option(
    "-n",
    "--num-iterations",
    type=int,
    default=1,
    help="Number of times to run each scenario (for calculating averages)",
)
def evaluate_agent(agent_version: str, num_iterations: int) -> None:
    """Run all scenarios against a specific agent version."""
    try:
        run_agent_evaluation(agent_version, num_iterations)
    except Exception as e:
        handle_cli_error(e, f"evaluation of {agent_version} agent")


@cli.command()
@click.option(
    "--scenario",
    type=click.Choice(
        [
            "happy-path",
            "recalled",
            "mismatched-card",
            "excessive-period",
            "adversarial-tone",
            "informational-query",
        ]
    ),
    required=True,
    help="Scenario to run across all agents",
)
@click.option(
    "-n",
    "--num-iterations",
    type=int,
    default=1,
    help="Number of times to run each agent (for calculating averages)",
)
def evaluate_scenario(scenario: str, num_iterations: int) -> None:
    """Run a specific scenario across all agent versions."""
    try:
        run_scenario_evaluation(scenario, num_iterations)
    except Exception as e:
        handle_cli_error(e, f"evaluation of {scenario} scenario")


@cli.command()
@click.option(
    "--output-file",
    type=str,
    help="Save results to JSON file",
)
@click.option(
    "--format",
    type=click.Choice(["summary", "detailed", "comparative"]),
    default="comparative",
    help="Output format for results",
)
@click.option(
    "-n",
    "--num-iterations",
    type=int,
    default=1,
    help="Number of times to run each scenario (for calculating averages)",
)
@click.option(
    "-p",
    "--parallel",
    type=int,
    default=1,
    help="Number of parallel workers (default: 1 for sequential execution)",
)
def evaluate_all(output_file: str | None, format: str, num_iterations: int, parallel: int) -> None:
    """Run comprehensive evaluation suite (6 agents × 6 scenarios = 36 evaluations)."""
    console.print("[bold blue]Running Comprehensive Evaluation Suite[/bold blue]")
    total_runs = 36 * num_iterations
    if num_iterations > 1:
        console.print(f"This will run 6 agents × 6 scenarios × {num_iterations} iterations = {total_runs} evaluations")
    else:
        console.print("This will run 6 agents × 6 scenarios = 36 evaluations")

    if parallel > 1:
        console.print(f"Using {parallel} parallel workers\n")
    else:
        console.print()

    try:
        # Auto-generate output filename if not provided
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = ensure_output_directory()
            output_file = os.path.join(output_dir, f"evaluation_results_{timestamp}.json")
            console.print(f"[dim]Results will be saved to: {output_file}[/dim]\n")

        agent_versions = ["no-instructions", "simple", "sop", "steering", "workflow"]
        all_results: dict[str, list[EvaluationResult]] = {av: [] for av in agent_versions}

        if parallel > 1:
            # Build list of all tasks
            tasks: list[tuple[str, EvaluationScenario, int]] = []
            for agent_version in agent_versions:
                for scenario in ALL_SCENARIOS:
                    for i in range(num_iterations):
                        tasks.append((agent_version, scenario, i))

            # Run in parallel with progress bar
            completed = 0
            failed = 0
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task_id = progress.add_task("Running evaluations...", total=len(tasks))

                with ThreadPoolExecutor(max_workers=parallel) as executor:
                    futures = {executor.submit(run_single_evaluation_task, task): task for task in tasks}

                    for future in as_completed(futures):
                        task_info = futures[future]
                        try:
                            agent_version, scenario_name, iteration, result = future.result()
                            all_results[agent_version].append(result)
                            completed += 1
                            status = "✓" if result.passed else "✗"
                            color = "green" if result.passed else "red"
                            desc = f"[{color}]{status}[/] {agent_version}/{scenario_name}"
                            progress.update(task_id, advance=1, description=desc)
                        except Exception as e:
                            failed += 1
                            agent_version = task_info[0]
                            scenario_name = task_info[1].name
                            logger.error(f"Task failed: {agent_version}/{scenario_name}: {e}")
                            # Add a failed result so it shows up in the report
                            failed_result = EvaluationResult(
                                agent_version=agent_version,
                                scenario_name=scenario_name,
                                passed=False,
                                score=0.0,
                                details={"error": str(e)},
                                token_usage=None,
                            )
                            all_results[agent_version].append(failed_result)
                            desc = f"[red]✗[/] {agent_version}/{scenario_name} (error)"
                            progress.update(task_id, advance=1, description=desc)

            console.print(f"\n[bold]Completed:[/bold] {completed} successful, {failed} failed")
        else:
            # Sequential execution (original behavior)
            runner = LibraryAgentEvaluationRunner()
            completed = 0
            failed = 0
            for agent_version in agent_versions:
                console.print(f"\n[bold cyan]Agent: {agent_version.upper()}[/bold cyan]")

                for scenario in ALL_SCENARIOS:
                    if num_iterations == 1:
                        console.print(f"  Scenario: [cyan]{scenario.name}[/cyan]")
                        result = run_scenario_with_retry(runner, agent_version, scenario)
                        all_results[agent_version].append(result)
                        completed += 1
                        print_run_result(result, prefix="    ")
                    else:
                        console.print(f"  Scenario: [cyan]{scenario.name}[/cyan] ({num_iterations} iterations)")
                        for i in range(num_iterations):
                            result = run_scenario_with_retry(runner, agent_version, scenario)
                            all_results[agent_version].append(result)
                            completed += 1
                            console.print(f"    [bold]Run {i + 1}:[/bold]")
                            print_run_result(result, prefix="      ")

        # Aggregate results if multiple iterations
        if num_iterations > 1:
            aggregated_results = aggregate_evaluation_results(all_results)
            # Generate and display report based on format
            if format == "detailed":
                print_aggregated_detailed_report(aggregated_results)
            elif format == "summary":
                print_aggregated_summary(aggregated_results)
            else:  # comparative
                print_aggregated_comparative_summary(aggregated_results)

            # Save aggregated results
            save_aggregated_results_to_file(aggregated_results, output_file)

            # Save summary to results-summary.md
            summary_file = os.path.join(os.path.dirname(output_file), "results-summary.md")
            save_summary_to_file(aggregated_results, summary_file, completed, failed)
        else:
            # Generate and display report based on format
            if format == "detailed":
                report = generate_comprehensive_report(all_results)
                print_comprehensive_report(report)
            elif format == "summary":
                # Just print basic summary
                total_evaluations = sum(len(results) for results in all_results.values())
                total_passed = sum(sum(1 for r in results if r.passed) for results in all_results.values())
                console.print("\n[bold]Overall Results:[/bold]")
                console.print(f"Total Evaluations: {total_evaluations}")
                console.print(f"Total Passed: {total_passed}")
                console.print(f"Pass Rate: {(total_passed / total_evaluations) * 100:.1f}%")
            else:  # comparative
                print_comparative_summary(all_results)

            # Always save to file (either provided or auto-generated)
            save_results_to_file(all_results, output_file)

    except Exception as e:
        handle_cli_error(e, "comprehensive evaluation")


@cli.command()
def list_agents() -> None:
    """List available agent versions and their descriptions."""
    console.print("[bold blue]Available Agent Versions:[/bold blue]\n")

    agents = [
        (
            "no-instructions",
            "No Instructions Agent",
            "Simple system prompt: 'You are an automated librarian assistant.'",
        ),
        (
            "simple",
            "Simple Instructions Agent",
            "System prompt with four behavioral rules",
        ),
        (
            "sop",
            "Agent SOP",
            "Uses generated Standard Operating Procedures in system prompt",
        ),
        (
            "steering",
            "Steering Agent",
            "Advanced control with steering providers and AgentCore policies",
        ),
        (
            "workflow",
            "Workflow Agent",
            "Sequential multi-agent workflow: gather info → renew → confirm",
        ),
    ]

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Version")
    table.add_column("Name")
    table.add_column("Description")

    for version, name, description in agents:
        table.add_row(version, name, description)

    console.print(table)


@cli.command()
def list_scenarios() -> None:
    """List available evaluation scenarios and their descriptions."""
    console.print("[bold blue]Available Evaluation Scenarios:[/bold blue]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Scenario")
    table.add_column("Description")
    table.add_column("Challenge")

    scenario_info = [
        ("happy-path", "Successful book renewal", "Normal workflow validation"),
        (
            "recalled",
            "Book status is RECALLED",
            "Workflow adherence - must not renew recalled books",
        ),
        (
            "mismatched-card",
            "User provides wrong library card",
            "Input validation - must use correct card number",
        ),
        (
            "excessive-period",
            "User requests 90-day renewal",
            "Parameter constraint - must limit to 30 days",
        ),
        (
            "adversarial-tone",
            "User asks agent to be rude",
            "Tone adherence - must maintain positive tone",
        ),
        (
            "informational-query",
            "User asks what books are checked out",
            "Task understanding - answer question without renewal",
        ),
    ]

    for scenario, description, challenge in scenario_info:
        table.add_row(scenario, description, challenge)

    console.print(table)


# Legacy command for backward compatibility
@cli.command(hidden=True)
@click.option(
    "--agent-version",
    type=click.Choice(["no-instructions", "simple", "sop", "steering"]),
    default="no-instructions",
    help="Agent version to run",
)
@click.option(
    "--scenario",
    type=click.Choice(["recalled", "mismatched-card", "excessive-period", "adversarial-tone", "informational-query"]),
    help="Evaluation scenario to run",
)
@click.option(
    "--evaluate-all",
    "evaluate_all_flag",
    is_flag=True,
    help="Run all evaluation combinations",
)
def main(agent_version: str, scenario: str | None, evaluate_all_flag: bool) -> None:
    """Legacy main command - use subcommands instead."""
    try:
        if evaluate_all_flag:
            # Call the evaluate_all function directly with default parameters
            console.print("[bold blue]Running Comprehensive Evaluation Suite[/bold blue]")
            console.print("This will run 5 agents × 5 scenarios = 25 evaluations\n")
            all_results = run_comprehensive_evaluation_suite()
            print_comparative_summary(all_results)
        elif scenario:
            run_single_evaluation(agent_version, scenario)
        else:
            run_interactive_mode(agent_version)
    except Exception as e:
        handle_cli_error(e, "legacy main command")


if __name__ == "__main__":
    cli()
