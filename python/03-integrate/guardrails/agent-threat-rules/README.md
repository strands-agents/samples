# Agent Threat Rules (ATR) Guardrail

Screen agent inputs and tool calls with [Agent Threat Rules](https://github.com/Agent-Threat-Rule/agent-threat-rules) (ATR), an open-source (MIT) detection ruleset for AI-agent threats. The check runs in-process with no API key, no network call, and no agent data leaving the host.

## Overview

### Sample Details

| Information            | Details                                                          |
|------------------------|------------------------------------------------------------------|
| **Agent Architecture** | Single-agent                                                     |
| **Native Tools**       | None                                                             |
| **Custom Tools**       | None                                                             |
| **MCP Servers**        | None                                                             |
| **Use Case Vertical**  | Security / Guardrails                                            |
| **Complexity**         | Basic                                                            |
| **Model Provider**     | Amazon Bedrock                                                   |
| **SDK Used**           | Strands Agents SDK                                               |

This sample adds a `HookProvider` that runs ATR detection rules at two enforcement points:

- `BeforeInvocationEvent` — scans the incoming user turn and cancels the invocation when a rule at or above `min_severity` matches.
- `BeforeToolCallEvent` — scans the tool arguments and cancels that tool call when a rule matches (for example, an injected exfiltration URL inside tool input).

How it differs from the other guardrail samples here: the WonderFence sample calls a hosted evaluation service, and the LlamaFirewall and NVIDIA NeMo samples run model-based scanners. ATR is fully local and deterministic (pattern rules, no model call, no outbound request), which fits regulated or data-residency-sensitive deployments. The samples are complementary — ATR can run alongside a model-based scanner as a fast, offline first layer.

Pass `shadow=True` to log matches without blocking, so you can measure rule hits before enforcing.

## Prerequisites

- Python 3.10+
- Amazon Bedrock access configured for Strands (see the SDK quickstart)

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

The demo sends a benign prompt (allowed) and a prompt-injection prompt (blocked by ATR before the model is called).

To use the hook in your own agent:

```python
from strands import Agent
from guardrail import ATRGuardrailHook

agent = Agent(hooks=[ATRGuardrailHook(min_severity="high")])
```

## Cleanup

No infrastructure is provisioned by this sample; no cleanup is required.
