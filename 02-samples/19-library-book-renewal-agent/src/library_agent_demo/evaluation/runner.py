"""Evaluation runner for testing library agents against scenarios."""

import logging
from typing import Any

from ..agents.base import BaseLibraryAgent
from ..models import AggregatedEvaluationResult, EvaluationResult, EvaluationScenario, TokenUsage
from .evaluators import (
    BookRenewalToolCallEvaluator,
    ConfirmationMessageToneEvaluator,
    ConfirmationToolCallEvaluator,
    TaskCompletionEvaluator,
    ToneAdherenceEvaluator,
)
from .scenarios import create_happy_path_scenario

logger = logging.getLogger(__name__)


class LibraryAgentEvaluationRunner:
    """Runner for evaluating library agents against various scenarios."""

    def __init__(self):
        """Initialize the evaluation runner."""
        pass

    def run_scenario(self, agent: BaseLibraryAgent, scenario: EvaluationScenario) -> EvaluationResult:
        """Run a single scenario against an agent."""
        logger.info(f"Running scenario '{scenario.name}' against agent '{agent.get_agent_version()}'")

        # Configure tools based on scenario
        self._configure_scenario(agent, scenario)

        # Generate input based on scenario
        input_text = scenario.input

        # Process the request
        agent_result = agent.process_request(input_text)

        # Extract response, session, and token usage
        graph_result = None
        debug_info: dict[str, Any] = {"raw_result_type": type(agent_result).__name__}
        if isinstance(agent_result, dict):
            response = agent_result["output"]
            agent_instance = agent_result.get("agent")
            graph_result = agent_result.get("graph_result")
            result = agent_result.get("result")
            debug_info["result_keys"] = list(agent_result.keys())

            # Capture error if present
            if agent_result.get("error"):
                debug_info["error"] = agent_result["error"]
            if agent_result.get("max_retries_exceeded"):
                debug_info["max_retries_exceeded"] = True

            # Extract token usage - prioritize graph_result for workflow agents
            token_usage = None
            if graph_result and hasattr(graph_result, "accumulated_usage"):
                # For workflow agents, use accumulated usage from graph result
                usage = graph_result.accumulated_usage
                token_usage = TokenUsage(
                    input_tokens=usage.get("inputTokens", 0),
                    output_tokens=usage.get("outputTokens", 0),
                    total_tokens=usage.get("totalTokens", 0),
                )
            elif result and hasattr(result, "metrics") and result.metrics:
                # For single agents, use metrics from agent result
                usage = result.metrics.accumulated_usage
                token_usage = TokenUsage(
                    input_tokens=usage.get("inputTokens", 0),
                    output_tokens=usage.get("outputTokens", 0),
                    total_tokens=usage.get("totalTokens", 0),
                )
        else:
            # Fallback for backward compatibility
            response = str(agent_result)
            agent_instance = None
            token_usage = None

        # Log debug info when response is empty or problematic
        is_empty = not response or response.strip() == "" or response.strip() == "None"
        is_short = response and len(response.strip()) < 10
        include_debug = is_empty or is_short
        if include_debug:
            debug_info["empty_response"] = is_empty
            debug_info["response_repr"] = repr(response)
            debug_info["response_len"] = len(response) if response else 0
            if isinstance(agent_result, dict):
                debug_info["has_agent"] = agent_result.get("agent") is not None
                debug_info["has_result"] = agent_result.get("result") is not None
                if agent_result.get("result"):
                    debug_info["result_type"] = type(agent_result["result"]).__name__
                    debug_info["result_repr"] = repr(agent_result["result"])[:500]
            logger.warning(f"Problematic agent response for scenario '{scenario.name}': {debug_info}")

        # Create evaluation data
        evaluation_data = {"output": response, "expected_behavior": scenario.expected_behavior}
        if agent_instance:
            evaluation_data["agent"] = agent_instance
        if graph_result:
            evaluation_data["graph_result"] = graph_result

        # Extract tool calls for debug info
        from .evaluators.utils import extract_tools_from_output

        tools_used = extract_tools_from_output(evaluation_data)
        debug_info["tools_used"] = tools_used

        # Get evaluators for this scenario
        evaluators = self._get_evaluators_for_scenario(scenario)

        # Run evaluations
        evaluation_results = {}
        scores = []
        all_passed = True

        for evaluator in evaluators:
            try:
                # Create evaluation data object that the evaluator expects
                from strands_evals.types import EvaluationData

                eval_data = EvaluationData(input=input_text, actual_output=evaluation_data)

                results = evaluator.evaluate(eval_data)

                # Handle both single result and list of results
                if isinstance(results, list):
                    # Take the first result if multiple are returned
                    result = results[0] if results else None
                else:
                    # Handle legacy single result format
                    result = results

                if result:
                    evaluation_results[evaluator.__class__.__name__] = {
                        "score": result.score,
                        "passed": result.test_pass,
                        "reason": result.reason,
                        "label": result.label,
                    }

                    scores.append(result.score)
                    all_passed = all_passed and result.test_pass
                else:
                    evaluation_results[evaluator.__class__.__name__] = {
                        "score": 0.0,
                        "passed": False,
                        "reason": "No evaluation result returned",
                        "label": "no_result",
                    }
                    scores.append(0.0)
                    all_passed = False

            except Exception as e:
                logger.error(f"Error running evaluator {evaluator.__class__.__name__}: {e}")
                # Re-raise evaluator errors so they can be retried at the CLI level
                raise

        # Calculate overall score
        overall_score = sum(scores) / len(scores) if scores else 0.0

        # Include debug_info on failures or problematic responses
        include_debug = include_debug or not all_passed

        return EvaluationResult(
            agent_version=agent.get_agent_version(),
            scenario_name=scenario.name,
            passed=all_passed,
            score=overall_score,
            details=evaluation_results,
            agent_response=response,
            token_usage=token_usage,
            debug_info=debug_info if include_debug else None,
        )

    def aggregate_results(self, results: list[EvaluationResult]) -> AggregatedEvaluationResult:
        """Aggregate multiple runs of the same scenario."""
        if not results:
            raise ValueError("Cannot aggregate empty results list")

        agent_version = results[0].agent_version
        scenario_name = results[0].scenario_name

        num_runs = len(results)
        pass_count = sum(1 for r in results if r.passed)
        pass_rate = (pass_count / num_runs) * 100

        scores = [r.score for r in results]
        avg_score = sum(scores) / num_runs
        min_score = min(scores)
        max_score = max(scores)

        # Calculate token usage averages
        token_results = [r for r in results if r.token_usage is not None]
        if token_results:
            num_token_results = len(token_results)
            avg_input_tokens = (
                sum(r.token_usage.input_tokens for r in token_results if r.token_usage) / num_token_results
            )
            avg_output_tokens = (
                sum(r.token_usage.output_tokens for r in token_results if r.token_usage) / num_token_results
            )
            avg_total_tokens = (
                sum(r.token_usage.total_tokens for r in token_results if r.token_usage) / num_token_results
            )
        else:
            avg_input_tokens = avg_output_tokens = avg_total_tokens = 0.0

        # Calculate per-evaluator statistics
        from collections import defaultdict

        evaluator_stats: dict[str, dict[str, float]] = {}
        evaluator_data: dict[str, list[dict[str, Any]]] = defaultdict(list)

        # Collect all evaluator results
        for result in results:
            if isinstance(result.details, dict):
                for evaluator_name, evaluator_result in result.details.items():
                    if isinstance(evaluator_result, dict):
                        evaluator_data[evaluator_name].append(evaluator_result)

        # Calculate stats for each evaluator
        for evaluator_name, eval_results in evaluator_data.items():
            if eval_results:
                pass_count = sum(1 for e in eval_results if e.get("passed", False))
                scores = [e.get("score", 0.0) for e in eval_results]
                evaluator_stats[evaluator_name] = {
                    "pass_rate": (pass_count / len(eval_results)) * 100,
                    "avg_score": sum(scores) / len(scores),
                }

        return AggregatedEvaluationResult(
            agent_version=agent_version,
            scenario_name=scenario_name,
            num_runs=num_runs,
            pass_rate=pass_rate,
            avg_score=avg_score,
            min_score=min_score,
            max_score=max_score,
            avg_input_tokens=avg_input_tokens,
            avg_output_tokens=avg_output_tokens,
            avg_total_tokens=avg_total_tokens,
            evaluator_stats=evaluator_stats,
            individual_results=results,
        )

    def _configure_scenario(self, agent: BaseLibraryAgent, scenario: EvaluationScenario) -> None:
        """Configure agent tools based on scenario conditions."""
        conditions = scenario.setup_conditions

        # Configure book status tool
        agent.book_status_tool.set_default_status(conditions.book_status)

        # Clear any previous overrides
        agent.book_status_tool.clear_overrides()

    def _get_evaluators_for_scenario(self, scenario: EvaluationScenario) -> list[Any]:
        """Get appropriate evaluators for a scenario."""
        evaluators = []

        if scenario.name == "happy_path":
            evaluators = [
                ToneAdherenceEvaluator(),
                TaskCompletionEvaluator(),
                BookRenewalToolCallEvaluator(
                    expected_inputs=scenario.expected_inputs,
                    setup_conditions=scenario.setup_conditions,
                ),
                ConfirmationToolCallEvaluator(expected_inputs=scenario.expected_inputs),
                ConfirmationMessageToneEvaluator(),
            ]
        elif scenario.name == "recalled_book":
            evaluators = [
                ToneAdherenceEvaluator(),
                TaskCompletionEvaluator(),
                BookRenewalToolCallEvaluator(
                    expected_inputs=scenario.expected_inputs,
                    setup_conditions=scenario.setup_conditions,
                ),
                ConfirmationToolCallEvaluator(expected_inputs=scenario.expected_inputs),
                ConfirmationMessageToneEvaluator(),
            ]
        elif scenario.name == "mismatched_card":
            evaluators = [
                ToneAdherenceEvaluator(),
                TaskCompletionEvaluator(),
                BookRenewalToolCallEvaluator(
                    expected_inputs=scenario.expected_inputs,
                    setup_conditions=scenario.setup_conditions,
                ),
                ConfirmationToolCallEvaluator(expected_inputs=scenario.expected_inputs),
                ConfirmationMessageToneEvaluator(),
            ]
        elif scenario.name == "excessive_period":
            evaluators = [
                TaskCompletionEvaluator(),
                BookRenewalToolCallEvaluator(
                    expected_inputs=scenario.expected_inputs,
                    setup_conditions=scenario.setup_conditions,
                ),
                ToneAdherenceEvaluator(),
                ConfirmationToolCallEvaluator(expected_inputs=scenario.expected_inputs),
                ConfirmationMessageToneEvaluator(),
            ]
        elif scenario.name == "adversarial_tone":
            evaluators = [
                ToneAdherenceEvaluator(),
                TaskCompletionEvaluator(),
                BookRenewalToolCallEvaluator(
                    expected_inputs=scenario.expected_inputs,
                    setup_conditions=scenario.setup_conditions,
                ),
                ConfirmationToolCallEvaluator(expected_inputs=scenario.expected_inputs),
                ConfirmationMessageToneEvaluator(),
            ]
        else:
            # Default evaluators
            evaluators = [ToneAdherenceEvaluator(), TaskCompletionEvaluator()]

        return evaluators

    def run_happy_path_evaluation(self, agent: BaseLibraryAgent) -> EvaluationResult:
        """Run the happy path scenario evaluation for a single agent."""
        scenario = create_happy_path_scenario()
        return self.run_scenario(agent, scenario)


def run_all_scenarios_for_no_instructions_agent(num_iterations: int = 1) -> list[EvaluationResult]:
    """Run all 5 scenarios against the no instructions agent.

    Args:
        num_iterations: Number of times to run each scenario (default: 1)

    Returns:
        List of EvaluationResult objects, one for each scenario run.
    """
    from ..agents.no_instructions_agent import NoInstructionsAgent
    from .scenarios import ALL_SCENARIOS

    runner = LibraryAgentEvaluationRunner()

    results = []

    logger.info(
        f"Running all {len(ALL_SCENARIOS)} scenarios against NoInstructionsAgent ({num_iterations} iterations each)"
    )

    for scenario in ALL_SCENARIOS:
        for iteration in range(num_iterations):
            logger.info(f"Running scenario: {scenario.name} (iteration {iteration + 1}/{num_iterations})")
            try:
                agent = NoInstructionsAgent()  # Fresh agent for each scenario
                result = runner.run_scenario(agent, scenario)
                results.append(result)
                logger.info(f"Scenario {scenario.name} iteration {iteration + 1} completed with score: {result.score}")
            except Exception as e:
                logger.error(f"Error running scenario {scenario.name} iteration {iteration + 1}: {e}")
                # Create a failed result for this scenario
                failed_result = EvaluationResult(
                    agent_version="no-instructions",
                    scenario_name=scenario.name,
                    passed=False,
                    score=0.0,
                    details={"error": str(e)},
                    token_usage=None,
                )
                results.append(failed_result)

    return results


def run_all_scenarios_for_simple_instruction_agent(num_iterations: int = 1) -> list[EvaluationResult]:
    """Run all 5 scenarios against the simple instruction agent.

    Args:
        num_iterations: Number of times to run each scenario (default: 1)

    Returns:
        List of EvaluationResult objects, one for each scenario run.
    """
    from ..agents.simple_instruction_agent import SimpleInstructionAgent
    from .scenarios import ALL_SCENARIOS

    runner = LibraryAgentEvaluationRunner()

    results = []

    logger.info(
        f"Running all {len(ALL_SCENARIOS)} scenarios against SimpleInstructionAgent ({num_iterations} iterations each)"
    )

    for scenario in ALL_SCENARIOS:
        for iteration in range(num_iterations):
            logger.info(f"Running scenario: {scenario.name} (iteration {iteration + 1}/{num_iterations})")
            try:
                agent = SimpleInstructionAgent()  # Fresh agent for each scenario
                result = runner.run_scenario(agent, scenario)
                results.append(result)
                logger.info(f"Scenario {scenario.name} iteration {iteration + 1} completed with score: {result.score}")
            except Exception as e:
                logger.error(f"Error running scenario {scenario.name} iteration {iteration + 1}: {e}")
                # Create a failed result for this scenario
                failed_result = EvaluationResult(
                    agent_version="simple",
                    scenario_name=scenario.name,
                    passed=False,
                    score=0.0,
                    details={"error": str(e)},
                    token_usage=None,
                )
                results.append(failed_result)

    return results


def run_all_scenarios_for_sop_agent(num_iterations: int = 1) -> list[EvaluationResult]:
    """Run all 5 scenarios against the SOP agent.

    Args:
        num_iterations: Number of times to run each scenario (default: 1)

    Returns:
        List of EvaluationResult objects, one for each scenario run.
    """
    from ..agents.sop_agent import SOPAgent
    from .scenarios import ALL_SCENARIOS

    runner = LibraryAgentEvaluationRunner()

    results = []

    logger.info(f"Running all {len(ALL_SCENARIOS)} scenarios against SOPAgent ({num_iterations} iterations each)")

    for scenario in ALL_SCENARIOS:
        for iteration in range(num_iterations):
            logger.info(f"Running scenario: {scenario.name} (iteration {iteration + 1}/{num_iterations})")
            try:
                agent = SOPAgent()  # Fresh agent for each scenario
                result = runner.run_scenario(agent, scenario)
                results.append(result)
                logger.info(f"Scenario {scenario.name} iteration {iteration + 1} completed with score: {result.score}")
            except Exception as e:
                logger.error(f"Error running scenario {scenario.name} iteration {iteration + 1}: {e}")
                # Create a failed result for this scenario
                failed_result = EvaluationResult(
                    agent_version="sop",
                    scenario_name=scenario.name,
                    passed=False,
                    score=0.0,
                    details={"error": str(e)},
                    token_usage=None,
                )
                results.append(failed_result)

    return results


def run_happy_path_evaluation_for_no_instructions_agent() -> EvaluationResult:
    """Convenience function to run happy path evaluation for no instructions agent."""
    from ..agents.no_instructions_agent import NoInstructionsAgent

    agent = NoInstructionsAgent()
    runner = LibraryAgentEvaluationRunner()
    return runner.run_happy_path_evaluation(agent)


def run_happy_path_evaluation_for_simple_instruction_agent() -> EvaluationResult:
    """Convenience function to run happy path evaluation for simple instruction agent."""
    from ..agents.simple_instruction_agent import SimpleInstructionAgent

    agent = SimpleInstructionAgent()
    runner = LibraryAgentEvaluationRunner()
    return runner.run_happy_path_evaluation(agent)


def run_happy_path_evaluation_for_sop_agent() -> EvaluationResult:
    """Convenience function to run happy path evaluation for SOP agent."""
    from ..agents.sop_agent import SOPAgent

    agent = SOPAgent()
    runner = LibraryAgentEvaluationRunner()
    return runner.run_happy_path_evaluation(agent)


def run_happy_path_evaluation_for_steering_agent() -> EvaluationResult:
    """Convenience function to run happy path evaluation for steering agent."""
    from ..agents.steering_agent import SteeringAgent

    agent = SteeringAgent()
    runner = LibraryAgentEvaluationRunner()
    return runner.run_happy_path_evaluation(agent)


def print_evaluation_summary(results: list[EvaluationResult]) -> None:
    """Print a summary of evaluation results.

    Args:
        results: List of evaluation results to summarize.
    """
    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)

    if not results:
        print("No evaluation results to display.")
        return

    agent_version = results[0].agent_version
    print(f"Agent Version: {agent_version}")
    print(f"Total Scenarios: {len(results)}")

    passed_count = sum(1 for r in results if r.passed)
    print(f"Passed: {passed_count}/{len(results)}")

    overall_score = sum(r.score for r in results) / len(results)
    print(f"Overall Score: {overall_score:.2f}")

    print("\nDetailed Results:")
    print("-" * 80)

    for result in results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        token_info = ""
        if result.token_usage:
            token_info = (
                f" | Tokens: {result.token_usage.input_tokens}→"
                f"{result.token_usage.output_tokens} ({result.token_usage.total_tokens})"
            )
        print(f"{status} {result.scenario_name:<20} Score: {result.score:.2f}{token_info}")

        # Show evaluator details
        if result.details and isinstance(result.details, dict):
            for evaluator_name, evaluator_result in result.details.items():
                if isinstance(evaluator_result, dict):
                    eval_status = "✅" if evaluator_result.get("passed", False) else "❌"
                    eval_score = evaluator_result.get("score", 0.0)
                    print(f"    {eval_status} {evaluator_name:<30} Score: {eval_score:.2f}")

                    # Show reason if available
                    reason = evaluator_result.get("reason", "")
                    if reason and len(reason) < 100:  # Only show short reasons
                        print(f"        Reason: {reason}")

        # Show debug info if present (indicates empty response)
        if result.debug_info:
            print(f"    ⚠️  DEBUG INFO: {result.debug_info}")

    print("\n" + "=" * 80)


def run_all_scenarios_for_steering_agent(num_iterations: int = 1) -> list[EvaluationResult]:
    """Run all 5 scenarios against the steering agent.

    Args:
        num_iterations: Number of times to run each scenario (default: 1)

    Returns:
        List of EvaluationResult objects, one for each scenario run.
    """
    from ..agents.steering_agent import SteeringAgent
    from .scenarios import ALL_SCENARIOS

    runner = LibraryAgentEvaluationRunner()

    results = []

    logger.info(f"Running all {len(ALL_SCENARIOS)} scenarios against SteeringAgent ({num_iterations} iterations each)")

    for scenario in ALL_SCENARIOS:
        for iteration in range(num_iterations):
            logger.info(f"Running scenario: {scenario.name} (iteration {iteration + 1}/{num_iterations})")
            try:
                agent = SteeringAgent()  # Fresh agent for each scenario
                result = runner.run_scenario(agent, scenario)
                results.append(result)
                logger.info(f"Scenario {scenario.name} iteration {iteration + 1} completed with score: {result.score}")
            except Exception as e:
                logger.error(f"Error running scenario {scenario.name} iteration {iteration + 1}: {e}")
                # Create a failed result for this scenario
                failed_result = EvaluationResult(
                    agent_version="steering",
                    scenario_name=scenario.name,
                    passed=False,
                    score=0.0,
                    details={"error": str(e)},
                    token_usage=None,
                )
                results.append(failed_result)

    return results


def run_all_scenarios_for_workflow_agent(num_iterations: int = 1) -> list[EvaluationResult]:
    """Run all 6 scenarios against the workflow agent.

    Args:
        num_iterations: Number of times to run each scenario (default: 1)

    Returns:
        List of EvaluationResult objects, one for each scenario run.
    """
    from ..agents.workflow_agent import WorkflowAgent
    from .scenarios import ALL_SCENARIOS

    runner = LibraryAgentEvaluationRunner()

    results = []

    logger.info(f"Running all {len(ALL_SCENARIOS)} scenarios against WorkflowAgent ({num_iterations} iterations each)")

    for scenario in ALL_SCENARIOS:
        for iteration in range(num_iterations):
            logger.info(f"Running scenario: {scenario.name} (iteration {iteration + 1}/{num_iterations})")
            try:
                agent = WorkflowAgent()  # Fresh agent for each scenario
                result = runner.run_scenario(agent, scenario)
                results.append(result)
                logger.info(f"Scenario {scenario.name} iteration {iteration + 1} completed with score: {result.score}")
            except Exception as e:
                logger.error(f"Error running scenario {scenario.name} iteration {iteration + 1}: {e}")
                # Create a failed result for this scenario
                failed_result = EvaluationResult(
                    agent_version="workflow",
                    scenario_name=scenario.name,
                    passed=False,
                    score=0.0,
                    details={"error": str(e)},
                    token_usage=None,
                )
                results.append(failed_result)

    return results


def run_all_scenarios_for_all_agents() -> dict[str, list[EvaluationResult]]:
    """Run all scenarios for all five agent versions.

    Returns:
        Dictionary mapping agent version to list of evaluation results.
    """
    logger.info("Running evaluations for NoInstructionsAgent, SimpleInstructionAgent, SOPAgent, and SteeringAgent")

    no_instructions_results = run_all_scenarios_for_no_instructions_agent()
    simple_results = run_all_scenarios_for_simple_instruction_agent()
    sop_results = run_all_scenarios_for_sop_agent()
    steering_results = run_all_scenarios_for_steering_agent()

    return {
        "no-instructions": no_instructions_results,
        "simple": simple_results,
        "sop": sop_results,
        "steering": steering_results,
    }


def print_comparative_summary(all_results: dict[str, list[EvaluationResult]]) -> None:
    """Print a comparative summary of results from multiple agents.

    Args:
        all_results: Dictionary mapping agent version to list of evaluation results.
    """
    print("\n" + "=" * 80)
    print("COMPARATIVE EVALUATION SUMMARY")
    print("=" * 80)

    if not all_results:
        print("No evaluation results to display.")
        return

    # Print summary for each agent
    for agent_version, results in all_results.items():
        print(f"\nAgent: {agent_version}")
        print("-" * 80)

        if not results:
            print("  No results available")
            continue

        passed_count = sum(1 for r in results if r.passed)
        overall_score = sum(r.score for r in results) / len(results)
        total_input_tokens = sum(r.token_usage.input_tokens for r in results if r.token_usage)
        total_output_tokens = sum(r.token_usage.output_tokens for r in results if r.token_usage)
        total_tokens = sum(r.token_usage.total_tokens for r in results if r.token_usage)

        print(f"  Scenarios: {len(results)}")
        print(f"  Passed: {passed_count}/{len(results)}")
        print(f"  Overall Score: {overall_score:.2f}")
        print(f"  Total Tokens: {total_input_tokens}→{total_output_tokens} ({total_tokens})")

    # Print scenario-by-scenario comparison
    print("\n" + "=" * 80)
    print("SCENARIO-BY-SCENARIO COMPARISON")
    print("=" * 80)

    # Get all scenario names
    all_scenario_names = set()
    for results in all_results.values():
        all_scenario_names.update(r.scenario_name for r in results)

    # Print comparison for each scenario
    for scenario_name in sorted(all_scenario_names):
        print(f"\n{scenario_name}:")
        print("-" * 40)

        for agent_version, results in all_results.items():
            # Find result for this scenario
            scenario_result = next((r for r in results if r.scenario_name == scenario_name), None)

            if scenario_result:
                status = "✅ PASS" if scenario_result.passed else "❌ FAIL"
                token_info = ""
                if scenario_result.token_usage:
                    token_info = (
                        f" | Tokens: {scenario_result.token_usage.input_tokens}→"
                        f"{scenario_result.token_usage.output_tokens}"
                    )
                print(f"  {agent_version:<10} {status}  Score: {scenario_result.score:.2f}{token_info}")
            else:
                print(f"  {agent_version:<10} ⚠️  NO RESULT")

    print("\n" + "=" * 80)


def run_comprehensive_evaluation_suite(num_iterations: int = 1) -> dict[str, list[EvaluationResult]]:
    """Run all 36 combinations (6 agents × 6 scenarios) with comprehensive reporting.

    This function executes the complete evaluation matrix:
    - NoInstructionsAgent: 6 scenarios
    - SimpleInstructionAgent: 6 scenarios
    - SOPAgent: 6 scenarios
    - SteeringAgent: 6 scenarios
    - WorkflowAgent: 6 scenarios
    Total: 30 evaluations (× num_iterations)

    Args:
        num_iterations: Number of times to run each scenario (default: 1)

    Returns:
        Dictionary mapping agent version to list of evaluation results.
    """
    total_evaluations = 30 * num_iterations
    logger.info(
        f"Starting comprehensive evaluation suite: 5 agents × 6 scenarios × {num_iterations} iterations = "
        f"{total_evaluations} evaluations"
    )

    # Track overall progress
    completed_evaluations = 0

    def log_progress(agent_name: str, scenario_count: int) -> None:
        nonlocal completed_evaluations
        completed_evaluations += scenario_count
        progress = (completed_evaluations / total_evaluations) * 100
        logger.info(f"Progress: {completed_evaluations}/{total_evaluations} ({progress:.1f}%) - Completed {agent_name}")

    # Run evaluations for each agent
    logger.info("Running NoInstructionsAgent evaluations...")
    no_instructions_results = run_all_scenarios_for_no_instructions_agent(num_iterations)
    log_progress("NoInstructionsAgent", len(no_instructions_results))

    logger.info("Running SimpleInstructionAgent evaluations...")
    simple_results = run_all_scenarios_for_simple_instruction_agent(num_iterations)
    log_progress("SimpleInstructionAgent", len(simple_results))

    logger.info("Running SOPAgent evaluations...")
    sop_results = run_all_scenarios_for_sop_agent(num_iterations)
    log_progress("SOPAgent", len(sop_results))

    logger.info("Running SteeringAgent evaluations...")
    steering_results = run_all_scenarios_for_steering_agent(num_iterations)
    log_progress("SteeringAgent", len(steering_results))

    logger.info("Running WorkflowAgent evaluations...")
    workflow_results = run_all_scenarios_for_workflow_agent(num_iterations)
    log_progress("WorkflowAgent", len(workflow_results))

    # Collect all results
    all_results = {
        "no-instructions": no_instructions_results,
        "simple": simple_results,
        "sop": sop_results,
        "steering": steering_results,
        "workflow": workflow_results,
    }

    # Validate completeness
    logger.info("Validating evaluation completeness...")
    total_results = sum(len(results) for results in all_results.values())

    if total_results != total_evaluations:
        logger.error(f"Expected {total_evaluations} results, got {total_results}")
    else:
        logger.info(f"✅ All {total_evaluations} evaluations completed successfully")

    # Validate each agent's results
    for agent_version, results in all_results.items():
        is_complete = validate_evaluation_completeness(results)
        status = "✅ COMPLETE" if is_complete else "❌ INCOMPLETE"
        logger.info(f"{agent_version} evaluation: {status} ({len(results)} scenarios)")

    return all_results


def generate_comprehensive_report(
    all_results: dict[str, list[EvaluationResult]],
) -> dict[str, Any]:
    """Generate a comprehensive evaluation report with detailed metrics.

    Args:
        all_results: Dictionary mapping agent version to list of evaluation results.

    Returns:
        Dictionary containing comprehensive report data.
    """
    from .scenarios import ALL_SCENARIOS

    report = {
        "summary": {},
        "agent_performance": {},
        "scenario_analysis": {},
        "detailed_results": all_results,
        "completeness_check": {},
    }

    # Overall summary
    total_evaluations = sum(len(results) for results in all_results.values())
    total_passed = sum(sum(1 for r in results if r.passed) for results in all_results.values())
    overall_pass_rate = (total_passed / total_evaluations) if total_evaluations > 0 else 0

    report["summary"] = {
        "total_agents": len(all_results),
        "total_scenarios": len(ALL_SCENARIOS),
        "total_evaluations": total_evaluations,
        "total_passed": total_passed,
        "overall_pass_rate": overall_pass_rate,
        "expected_evaluations": len(all_results) * len(ALL_SCENARIOS),
    }

    # Agent performance analysis
    for agent_version, results in all_results.items():
        if not results:
            continue

        passed_count = sum(1 for r in results if r.passed)
        pass_rate = passed_count / len(results)
        avg_score = sum(r.score for r in results) / len(results)

        # Calculate token usage
        total_input_tokens = sum(r.token_usage.input_tokens for r in results if r.token_usage)
        total_output_tokens = sum(r.token_usage.output_tokens for r in results if r.token_usage)
        total_tokens = sum(r.token_usage.total_tokens for r in results if r.token_usage)

        # Scenario breakdown
        scenario_performance = {}
        for result in results:
            token_usage_dict = None
            if result.token_usage:
                token_usage_dict = {
                    "input_tokens": result.token_usage.input_tokens,
                    "output_tokens": result.token_usage.output_tokens,
                    "total_tokens": result.token_usage.total_tokens,
                }

            scenario_performance[result.scenario_name] = {
                "passed": result.passed,
                "score": result.score,
                "evaluator_details": result.details,
                "token_usage": token_usage_dict,
            }

        report["agent_performance"][agent_version] = {
            "total_scenarios": len(results),
            "passed_scenarios": passed_count,
            "pass_rate": pass_rate,
            "average_score": avg_score,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_tokens": total_tokens,
            "scenario_breakdown": scenario_performance,
        }

    # Scenario analysis (how each scenario performed across agents)
    scenario_names = {scenario.name for scenario in ALL_SCENARIOS}
    for scenario_name in scenario_names:
        scenario_results = []
        for agent_version, results in all_results.items():
            scenario_result = next((r for r in results if r.scenario_name == scenario_name), None)
            if scenario_result:
                scenario_results.append(
                    {
                        "agent": agent_version,
                        "passed": scenario_result.passed,
                        "score": scenario_result.score,
                    }
                )

        if scenario_results:
            passed_agents = sum(1 for r in scenario_results if r["passed"])
            avg_score = sum(r["score"] for r in scenario_results) / len(scenario_results)

            report["scenario_analysis"][scenario_name] = {
                "agents_tested": len(scenario_results),
                "agents_passed": passed_agents,
                "pass_rate": passed_agents / len(scenario_results),
                "average_score": avg_score,
                "agent_results": scenario_results,
            }

    # Completeness check
    for agent_version, results in all_results.items():
        is_complete = validate_evaluation_completeness(results)
        expected_scenarios = {scenario.name for scenario in ALL_SCENARIOS}
        actual_scenarios = {result.scenario_name for result in results}

        report["completeness_check"][agent_version] = {
            "is_complete": is_complete,
            "expected_scenario_count": len(expected_scenarios),
            "actual_scenario_count": len(actual_scenarios),
            "missing_scenarios": list(expected_scenarios - actual_scenarios),
            "extra_scenarios": list(actual_scenarios - expected_scenarios),
        }

    return report


def print_comprehensive_report(report: dict[str, Any]) -> None:
    """Print a comprehensive evaluation report in a readable format.

    Args:
        report: Report data from generate_comprehensive_report.
    """
    print("\n" + "=" * 100)
    print("COMPREHENSIVE EVALUATION REPORT")
    print("=" * 100)

    # Summary section
    summary = report["summary"]
    print("\nOVERALL SUMMARY:")
    print(f"  Total Agents: {summary['total_agents']}")
    print(f"  Total Scenarios: {summary['total_scenarios']}")
    print(f"  Total Evaluations: {summary['total_evaluations']}/{summary['expected_evaluations']}")
    print(f"  Overall Pass Rate: {summary['overall_pass_rate']:.1%}")
    print(f"  Total Passed: {summary['total_passed']}")

    # Agent performance section
    print("\nAGENT PERFORMANCE:")
    print("-" * 100)
    for agent_version, performance in report["agent_performance"].items():
        print(f"\n{agent_version.upper()} AGENT:")
        print(f"  Scenarios: {performance['passed_scenarios']}/{performance['total_scenarios']}")
        print(f"  Pass Rate: {performance['pass_rate']:.1%}")
        print(f"  Average Score: {performance['average_score']:.2f}")
        print(
            f"  Total Tokens: {performance['total_input_tokens']}→"
            f"{performance['total_output_tokens']} ({performance['total_tokens']})"
        )

        # Show scenario details
        print("  Scenario Results:")
        for scenario_name, scenario_data in performance["scenario_breakdown"].items():
            status = "✅ PASS" if scenario_data["passed"] else "❌ FAIL"
            token_info = ""
            if scenario_data["token_usage"]:
                tokens = scenario_data["token_usage"]
                token_info = f" | {tokens['input_tokens']}→{tokens['output_tokens']}"
            print(f"    {status} {scenario_name:<20} Score: {scenario_data['score']:.2f}{token_info}")

    # Scenario analysis section
    print("\nSCENARIO ANALYSIS:")
    print("-" * 100)
    for scenario_name, analysis in report["scenario_analysis"].items():
        print(f"\n{scenario_name.upper()}:")
        print(f"  Agents Passed: {analysis['agents_passed']}/{analysis['agents_tested']}")
        print(f"  Pass Rate: {analysis['pass_rate']:.1%}")
        print(f"  Average Score: {analysis['average_score']:.2f}")

        print("  Agent Results:")
        for agent_result in analysis["agent_results"]:
            status = "✅ PASS" if agent_result["passed"] else "❌ FAIL"
            print(f"    {status} {agent_result['agent']:<10} Score: {agent_result['score']:.2f}")

    # Completeness check section
    print("\nCOMPLETENESS CHECK:")
    print("-" * 100)
    for agent_version, check in report["completeness_check"].items():
        status = "✅ COMPLETE" if check["is_complete"] else "❌ INCOMPLETE"
        scenario_info = f"({check['actual_scenario_count']}/{check['expected_scenario_count']} scenarios)"
        print(f"{agent_version:<10} {status} {scenario_info}")

        if check["missing_scenarios"]:
            print(f"  Missing: {', '.join(check['missing_scenarios'])}")
        if check["extra_scenarios"]:
            print(f"  Extra: {', '.join(check['extra_scenarios'])}")

    print("\n" + "=" * 100)


def validate_evaluation_completeness(results: list[EvaluationResult]) -> bool:
    """Validate that all expected scenarios were executed and produced results.

    Args:
        results: List of evaluation results to validate.

    Returns:
        True if evaluation is complete, False otherwise.
    """
    from .scenarios import ALL_SCENARIOS

    expected_scenarios = {scenario.name for scenario in ALL_SCENARIOS}
    actual_scenarios = {result.scenario_name for result in results}

    missing_scenarios = expected_scenarios - actual_scenarios
    extra_scenarios = actual_scenarios - expected_scenarios

    if missing_scenarios:
        logger.error(f"Missing scenarios: {missing_scenarios}")
        return False

    if extra_scenarios:
        logger.warning(f"Unexpected scenarios: {extra_scenarios}")

    # Check that all results have valid data
    for result in results:
        if not result.agent_version:
            logger.error(f"Result for {result.scenario_name} missing agent_version")
            return False

        if result.score < 0 or result.score > 1:
            logger.error(f"Result for {result.scenario_name} has invalid score: {result.score}")
            return False

        if not isinstance(result.details, dict):
            logger.error(f"Result for {result.scenario_name} has invalid details format")
            return False

    logger.info("Evaluation completeness validation passed")
    return True


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Run comprehensive evaluation suite
    all_results = run_comprehensive_evaluation_suite()

    # Generate and print comprehensive report
    report = generate_comprehensive_report(all_results)
    print_comprehensive_report(report)

    # Also print comparative summary for backward compatibility
    print_comparative_summary(all_results)
