# Tutorial 21: Observability & Debugging

Learn how to gain full visibility into your Strands agent's behavior using the
SDK's built-in telemetry. This tutorial covers tracing, debugging common agent
issues, exporting telemetry to production backends, and adding custom metrics —
using the `StrandsTelemetry` API that ships with the Strands Agents SDK.

## Tutorial Details

| | |
|---|---|
| Strands Features | `StrandsTelemetry`, `setup_console_exporter()`, `setup_otlp_exporter()`, span attributes, trace hierarchy |
| Agent Pattern | Single agent with custom tools exercising tracing and debugging scenarios |
| Tools | Small custom tools defined inline (calculator, flaky API simulator, token-heavy generator) |
| Model | Amazon Nova Lite on Amazon Bedrock (any Strands-supported model works) |

## What You'll Learn

By completing this tutorial, you will be able to:

- **Basics (Notebook 01):** Configure `StrandsTelemetry` with a single API call and
  run your first traced agent invocation
- **Trace Hierarchy (Notebook 02):** Read the Agent → Cycle → Model → Tool span
  hierarchy to understand exactly how your agent executes
- **Debugging (Notebook 03):** Find tool failures via error spans and detect context
  window pressure by tracking token growth across cycles
- **Backend Export (Notebook 04):** Export traces to CloudWatch, Langfuse, or Jaeger
  by changing a single environment variable
- **Production (Notebook 05):** Add custom span attributes, create metrics for
  aggregate monitoring, and configure `BatchSpanProcessor` for minimal latency impact

## Prerequisites

Before starting this tutorial, ensure you have:

1. **Python 3.10+** installed

2. **AWS credentials configured** for Bedrock model access:
   ```bash
   aws configure
   # Or set AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY environment variables
   ```

3. **Dependencies installed:**
   ```bash
   pip install -r requirements.txt
   ```

4. *(Optional)* **Docker** for running local backends (Jaeger):
   ```bash
   docker run --rm -d --name jaeger \
     -p 4318:4318 -p 16686:16686 \
     jaegertracing/all-in-one:latest
   ```

5. *(Optional)* **Langfuse account** for cloud LLM observability export

## How is this different from the existing `08-observability` on main?

The existing `08-observability` sample on the `main` branch focuses on **Langfuse + RAGAS
evaluation** — it requires deploying AWS infrastructure (OpenSearch, DynamoDB) and
evaluates agent responses using the RAGAS framework.

This tutorial (21-observability-debugging) takes a different approach: it focuses on
**tracing and debugging** using the Strands SDK's built-in `StrandsTelemetry` class.
This gives you:

- Zero infrastructure required to start (console exporter works immediately)
- Model-agnostic implementation (works with any Strands-supported provider)
- Debugging-first approach (tool failures, context pressure, unexpected behavior)
- Multiple backend options via a single OTLP configuration change
- Testable in isolation without deploying any AWS resources

## Tutorial Structure

```
python/01-learn/21-observability-debugging/
├── README.md                    # This file — overview, prerequisites, structure
├── requirements.txt             # Python dependencies for all notebooks
├── trace_utils.py               # Shared trace formatting and analysis helpers
├── 01_tracing_setup.ipynb       # Configure telemetry and first traced invocation
├── 02_trace_hierarchy.ipynb     # Understand the span hierarchy
├── 03_debugging_tools.ipynb     # Debug tool failures and context pressure
├── 04_backend_export.ipynb      # Export to CloudWatch, Langfuse, Jaeger
└── 05_custom_metrics.ipynb      # Custom attributes, metrics, production config
```

### Notebook Progression

Each notebook builds on the prior one, but can be understood independently if you
read the setup cell at the top:

1. **01_tracing_setup.ipynb** — Start here. Learn how `StrandsTelemetry` manages the
   global tracer and how every `Agent` instance automatically picks it up. Run your
   first traced invocation and capture spans programmatically.

2. **02_trace_hierarchy.ipynb** — Understand the four span types (Agent, Cycle, Model
   Invoke, Tool) and their parent-child relationships. Use `trace_utils.py` to
   format and summarize traces.

3. **03_debugging_tools.ipynb** — Two critical scenarios: finding tool failures via
   error spans (status, exception events, recovery behavior) and detecting context
   window pressure by monitoring token growth across cycles.

4. **04_backend_export.ipynb** — Switch from console output to production backends.
   The same `setup_otlp_exporter()` call works with CloudWatch (via ADOT), Langfuse,
   Jaeger, and any OTLP-compatible backend.

5. **05_custom_metrics.ipynb** — Add domain-specific span attributes, create counters
   and histograms for aggregate monitoring, and configure `BatchSpanProcessor` for
   production deployments.

## Installation

1. Create and activate a virtual environment:
   ```bash
   cd python/01-learn/21-observability-debugging
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure AWS credentials for Bedrock access:
   ```bash
   export AWS_DEFAULT_REGION=us-east-1
   # Ensure your AWS credentials are configured (via AWS CLI, environment variables, or IAM role)
   ```

4. Launch Jupyter:
   ```bash
   jupyter notebook
   ```

## A Note on Logging

The Strands Agents SDK observability framework covers three telemetry primitives:
**Traces**, **Metrics**, and **Logs**. This tutorial focuses on Traces (notebooks
01–04) and Metrics (notebook 05). For logging configuration, refer to the
[SDK Logs documentation](https://strandsagents.com/docs/user-guide/observability-evaluation/logs/).

## Related Tutorials

### Prior Learning

- [Tutorial 01 - First Agent](../01-first-agent) — Basic agent creation
- [Tutorial 02 - Tools and MCP](../02-tools-and-mcp) — Tool definition and usage
- [Tutorial 03 - Model Providers](../03-model-providers) — Model configuration

### Next Steps

- [Tutorial 05 - Guardrails](../05-guardrails) — Add content filtering alongside observability
- [SDK Observability Docs](https://strandsagents.com/docs/user-guide/observability-evaluation/observability/) — Full observability framework reference
- [SDK Traces Docs](https://strandsagents.com/docs/user-guide/observability-evaluation/traces/) — Deep dive into trace configuration
