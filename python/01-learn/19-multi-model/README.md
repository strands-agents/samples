# Tutorial 19: Multi-Model Agent Patterns

Learn how to combine multiple AI model providers within a single application using the Strands Agents SDK. This tutorial goes beyond basic provider switching (covered in tutorial 03) to teach runtime model swapping, heterogeneous multi-agent systems, cost-optimized routing, and fallback/retry patterns — production-ready techniques for building resilient, cost-efficient agent applications.

## Tutorial Details

| | |
|---|---|
| **Strands Features** | Runtime provider switching, multi-model configuration, model assignment per agent |
| **Agent Pattern** | Sequential pipeline, agents-as-tools, cost-based routing, fallback chains |
| **Tools** | `@tool` decorated functions, agent-tool wrappers |
| **Model** | BedrockModel (Claude Sonnet, Nova Lite, Nova Pro, Haiku), OpenAIModel (optional), AnthropicModel (optional) |

## What You'll Learn

By completing this tutorial, you will be able to:

- **Basics (Notebook 01):** Swap model providers on a running agent at runtime without changing tools or application logic
- **Intermediate (Notebook 02):** Build multi-agent systems where different agents use different model providers, including the agents-as-tools pattern for delegating complex work
- **Advanced (Notebook 03):** Implement cost-optimized routing that classifies task complexity and selects the most cost-effective model, plus fallback/retry patterns that keep your application running when a provider fails

## Prerequisites

Before starting this tutorial, ensure you have:

1. **Completed prior tutorials:**
   - [Tutorial 01 - First Agent](../01-first-agent/) — Basic agent creation
   - [Tutorial 02 - Tools and MCP](../02-tools-and-mcp/) — Tool definition and usage
   - [Tutorial 03 - Model Providers](../03-model-providers/) — Single-provider configuration

2. **Amazon Bedrock access** — Required for all examples. You need access to:
   - Claude Sonnet 4.5 (`us.anthropic.claude-sonnet-4-5-20250929-v1:0`)
   - Nova Lite (`us.amazon.nova-lite-v1:0`)
   - Nova Pro (`us.amazon.nova-pro-v1:0`)
   - Claude Haiku (`us.anthropic.claude-3-5-haiku-20241022-v1:0`)

3. **API keys for additional providers (optional):**
   - `OPENAI_API_KEY` — For OpenAI cross-provider examples in Notebook 02
   - `ANTHROPIC_API_KEY` — For Anthropic cross-provider examples in Notebook 02
   - *If these are unavailable, the tutorial provides Bedrock-only alternatives*

## Tutorial Structure

```
python/01-learn/19-multi-model/
├── README.md                  # This file — overview, prerequisites, structure
├── requirements.txt           # Python dependencies for all notebooks
├── 01_basics.ipynb            # Runtime provider switching
├── 02_intermediate.ipynb      # Multi-model multi-agent systems
└── 03_advanced.ipynb          # Cost-optimized routing + fallback patterns
```

### Notebook Progression

Each notebook is **independently runnable** — you don't need to execute them in order. However, the concepts build progressively:

1. **01_basics.ipynb** — Start here to understand how Strands decouples model configuration from application logic. Demonstrates swapping models at runtime while tools and prompts remain intact.

2. **02_intermediate.ipynb** — Builds on basics to show multi-agent architectures where different agents use different models. Covers sequential pipelines and the agents-as-tools pattern.

3. **03_advanced.ipynb** — Production patterns: a CostRouter that classifies task complexity and picks the cheapest adequate model, plus a FallbackHandler that retries with alternative providers on failure.

## Installation

1. **Create and activate a virtual environment:**

   ```bash
   cd python/01-learn/19-multi-model
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure AWS credentials** for Bedrock access:

   ```bash
   export AWS_DEFAULT_REGION=us-east-1
   # Ensure your AWS credentials are configured (via AWS CLI, environment variables, or IAM role)
   ```

4. **(Optional) Set additional provider keys:**

   ```bash
   export OPENAI_API_KEY=your-key-here
   export ANTHROPIC_API_KEY=your-key-here
   ```

5. **Launch Jupyter:**

   ```bash
   jupyter notebook
   ```

## Related Tutorials

### Prior Learning

- [Tutorial 03 - Model Providers](../03-model-providers/) — Covers single-provider configuration and basic model setup. Complete this first if you haven't already.

### Next Steps

- [Tutorial 10 - Agents as Tools](../10-agents-as-tools/) — Dive deeper into the agents-as-tools pattern introduced in Notebook 02
- [Tutorial 08 - Observability](../08-observability/) — Add tracing and monitoring to your multi-model systems for production visibility
