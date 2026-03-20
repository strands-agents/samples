"""Utility functions for evaluators."""

from strands_evals.extractors.tools_use_extractor import extract_agent_tools_used


def extract_tools_from_output(output: dict | None) -> list[dict]:
    """Extract tool calls from either agent or graph result.

    Args:
        output: The actual_output dict from evaluation, containing either 'agent' or 'graph_result'

    Returns:
        List of tool call dicts with name, input, tool_result, and is_error fields
    """
    if not output:
        return []

    # Check if this is a graph result
    graph_result = output.get("graph_result")
    if graph_result:
        # Extract tool calls from all graph nodes by accessing executor messages
        tools_used = []
        for node in graph_result.execution_order:
            if hasattr(node, "executor") and hasattr(node.executor, "messages"):
                node_tools = extract_agent_tools_used(node.executor.messages)  # type: ignore[attr-defined]
                tools_used.extend(node_tools)
        return tools_used
    else:
        # Original logic for non-graph agents
        agent_instance = output.get("agent")
        if agent_instance and hasattr(agent_instance, "messages"):
            return extract_agent_tools_used(agent_instance.messages)
        else:
            # Fallback: try to extract from trajectory if available
            trajectory = output.get("trajectory", [])
            return extract_agent_tools_used(trajectory) if trajectory else []
