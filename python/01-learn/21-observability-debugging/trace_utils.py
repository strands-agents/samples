"""Shared trace utilities for the Observability & Debugging tutorial.

This module provides helper functions for formatting and analyzing
OpenTelemetry trace spans. It is imported by all notebooks in this tutorial.
"""

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.trace import StatusCode


def format_trace_tree(spans: list[ReadableSpan]) -> str:
    """Format spans as an indented tree for notebook display.

    Args:
        spans: List of ReadableSpan objects from a completed trace.

    Returns:
        A formatted string showing the span tree with status icons,
        durations, and key attributes.

    Example:
        >>> spans = memory_exporter.get_finished_spans()
        >>> print(format_trace_tree(list(spans)))
        ✓ Agent (1523ms)
          ✓ Cycle (1520ms)
            ✓ Model Invoke (1200ms)
              └─ tokens: in=523 out=89
            ✓ calculator (3ms)
              └─ tool: calculator
    """
    output = []
    for span in spans:
        attrs = span.attributes or {}
        is_error = (
            span.status.status_code == StatusCode.ERROR
            or attrs.get("tool.status") == "error"
        )
        status_icon = "✗" if is_error else "✓"

        # Calculate duration
        if span.end_time and span.start_time:
            duration_ms = (span.end_time - span.start_time) / 1_000_000
            duration_str = f"{duration_ms:.0f}ms"
        else:
            duration_str = "N/A"

        output.append(f"  {status_icon} {span.name} ({duration_str})")

        # Token usage on model spans
        if "gen_ai.usage.input_tokens" in attrs:
            input_t = attrs["gen_ai.usage.input_tokens"]
            output_t = attrs.get("gen_ai.usage.output_tokens", 0)
            output.append(f"      └─ tokens: in={input_t} out={output_t}")

        # Tool info on tool spans
        if "gen_ai.tool.name" in attrs:
            tool_name = attrs["gen_ai.tool.name"]
            output.append(f"      └─ tool: {tool_name}")

        # Error details
        if span.status.status_code == StatusCode.ERROR:
            desc = span.status.description or "Unknown error"
            output.append(f"      └─ error: {desc}")
        elif attrs.get("tool.status") == "error":
            # Strands records tool errors as attributes
            for event in span.events:
                if event.name == "gen_ai.choice":
                    msg = event.attributes.get("message", "")
                    if "Error:" in str(msg):
                        output.append(f"      └─ error: {msg}")
                        break

        for event in span.events:
            if event.name == "exception":
                exc_type = event.attributes.get("exception.type", "")
                exc_msg = event.attributes.get("exception.message", "")
                output.append(f"      └─ exception: {exc_type}: {exc_msg}")

    return "\n".join(output)


def print_trace_summary(spans: list[ReadableSpan]) -> None:
    """Print a summary of trace statistics.

    Args:
        spans: List of ReadableSpan objects from a completed trace.

    Example:
        >>> spans = memory_exporter.get_finished_spans()
        >>> print_trace_summary(list(spans))
        📊 Trace Summary:
           Total spans: 5
           Error spans: 1
           Total duration: 1523ms
           Success rate: 80%
    """
    total_spans = len(spans)
    error_spans = sum(
        1 for s in spans
        if s.status.status_code == StatusCode.ERROR
        or (s.attributes or {}).get("tool.status") == "error"
    )

    # Duration from first to last span
    if spans:
        root = spans[0]
        if root.end_time and root.start_time:
            total_ms = (root.end_time - root.start_time) / 1_000_000
        else:
            total_ms = 0
    else:
        total_ms = 0

    print("📊 Trace Summary:")
    print(f"   Total spans: {total_spans}")
    print(f"   Error spans: {error_spans}")
    print(f"   Total duration: {total_ms:.0f}ms")
    print(f"   Success rate: {((total_spans - error_spans) / max(total_spans, 1)) * 100:.0f}%")


def find_error_spans(spans: list[ReadableSpan]) -> list[ReadableSpan]:
    """Filter spans to those with errors (status ERROR or tool.status == 'error').

    The Strands SDK may record tool failures as a span attribute
    (tool.status = "error") rather than setting the span's status_code to ERROR.
    This function checks both conditions.

    Args:
        spans: List of all spans from a trace.

    Returns:
        List of spans that indicate an error occurred.
    """
    error_spans = []
    for s in spans:
        if s.status.status_code == StatusCode.ERROR:
            error_spans.append(s)
        elif (s.attributes or {}).get("tool.status") == "error":
            error_spans.append(s)
    return error_spans


def analyze_token_growth(spans: list[ReadableSpan], context_limit: int = 200_000) -> dict:
    """Analyze token usage growth across model invoke spans.

    Extracts input/output token counts from model spans and calculates
    growth metrics useful for detecting context window pressure.

    Args:
        spans: List of all spans from a trace.
        context_limit: Model's context window size (default: 200K for Claude).

    Returns:
        Dictionary with growth analysis metrics.

    Example:
        >>> analysis = analyze_token_growth(list(spans))
        >>> print(f"Growth: {analysis['growth_pct']:.0f}%")
    """
    model_spans = []
    for span in spans:
        attrs = span.attributes or {}
        if "gen_ai.usage.input_tokens" in attrs:
            model_spans.append({
                "name": span.name,
                "input_tokens": attrs["gen_ai.usage.input_tokens"],
                "output_tokens": attrs.get("gen_ai.usage.output_tokens", 0),
            })

    if len(model_spans) < 2:
        return {"model_spans": model_spans, "growth": 0, "growth_pct": 0, "usage_pct": 0}

    first_input = model_spans[0]["input_tokens"]
    last_input = model_spans[-1]["input_tokens"]
    growth = last_input - first_input
    growth_pct = (growth / first_input * 100) if first_input > 0 else 0
    usage_pct = (last_input / context_limit) * 100

    return {
        "model_spans": model_spans,
        "first_input": first_input,
        "last_input": last_input,
        "growth": growth,
        "growth_pct": growth_pct,
        "usage_pct": usage_pct,
        "context_limit": context_limit,
    }
