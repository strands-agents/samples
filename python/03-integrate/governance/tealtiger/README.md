# Deterministic Governance for Strands Agents with TealTiger

Govern tool calls with policy-based authorization, PII detection, cost tracking, and a per-agent kill switch — all deterministic, sub-5ms, no LLM in the governance path.

## Overview

### Sample Details

| | |
|---|---|
| Agent Architecture | Single-agent |
| Native Tools | None |
| Custom Tools | `search_docs`, `write_report`, `delete_customer`, `send_email` |
| MCP Servers | None |
| Use Case Vertical | Security / Governance / Compliance |
| Complexity | Basic |
| Model Provider | Any (governance is model-agnostic) |
| SDK Used | Strands Agents SDK |

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│ Strands Agent                                             │
│                                                           │
│  Model decides tool call                                  │
│         │                                                 │
│         ▼                                                 │
│  BeforeToolCallEvent ──► TealTigerGovernanceHook          │
│                          ┌───────────────────────┐        │
│                          │ 1. Kill switch check  │ <5ms   │
│                          │ 2. Policy evaluation  │ determ. │
│                          │ 3. PII detection      │ no LLM │
│                          │ 4. Budget check       │        │
│                          └──────────┬────────────┘        │
│                                     │                     │
│                          ALLOW → tool executes            │
│                          DENY  → event.cancel_tool        │
└──────────────────────────────────────────────────────────┘
```

### Key Features

- **Policy-based tool allowlisting** — block unauthorized tools before execution
- **PII detection** — scan tool arguments for SSN, credit cards, emails, phone numbers
- **Session budget enforcement** — automatic deny when cost limit is reached
- **Kill switch** — freeze/unfreeze agents at runtime with zero policy setup
- **Structured audit trail** — every evaluation produces a decision record with correlation ID

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) for dependency management
- No API keys required — the demo runs deterministically without calling any LLM

## Setup

1. Install dependencies:

```bash
uv sync
```

Or with pip:

```bash
pip install -r requirements.txt
```

2. No `.env` configuration needed — this sample runs without API keys.

## Usage

Run the governance demo:

```bash
uv run main.py
```

Or:

```bash
python main.py
```

### Example Output

```
============================================================
  Strands Agents + TealTiger Governance Demo
============================================================

--- Scenario 1: search_docs (ALLOWED) ---
[TealTiger] ALLOWED | search_docs | 0.03ms | a1b2c3d4

--- Scenario 2: delete_customer (BLOCKED - not in allowlist) ---
[TealTiger] DENIED  | delete_customer | 0.02ms | e5f6a7b8
  cancel_tool = Tool 'delete_customer' not in allowlist

--- Scenario 3: send_email with SSN (BLOCKED - PII) ---
[TealTiger] DENIED  | send_email | 0.04ms | c9d0e1f2
  cancel_tool = PII detected in tool args: ssn

--- Scenario 4: Freeze agent (kill switch) ---
[TealTiger] FROZEN: Agent research-agent-prod
[TealTiger] DENIED  | search_docs | 0.01ms | 3a4b5c6d
  cancel_tool = Agent research-agent-prod is frozen

--- Scenario 5: Unfreeze agent ---
[TealTiger] UNFROZEN: Agent research-agent-prod
[TealTiger] ALLOWED | search_docs | 0.02ms | 7e8f9a0b
```

## Project Structure

| Component | File | Description |
|-----------|------|-------------|
| Entry point | `main.py` | Demo with 5 governance scenarios |
| Governance hook | `governance_hook.py` | TealTiger HookProvider for Strands |
| Dependencies | `requirements.txt` | Python package requirements |

## How It Works

The `TealTigerGovernanceHook` implements Strands' `HookProvider` interface and registers a callback on `BeforeToolCallEvent`. Every tool call passes through the governance evaluation before execution:

1. **Kill switch** — if the agent is frozen, deny immediately
2. **Tool allowlist** — check if the tool is in the permitted list
3. **PII detection** — regex scan tool arguments for sensitive data patterns
4. **Budget check** — verify session cost hasn't exceeded the limit

If any check fails in `enforce` mode, `event.cancel_tool` is set with the denial reason, and Strands cancels the tool execution.

## Governance Modes

| Mode | Behavior |
|------|----------|
| `observe` | Allow all, log decisions (zero-config visibility) |
| `monitor` | Allow all, log denials as warnings |
| `enforce` | Block denied actions via `event.cancel_tool` |

## Additional Resources

- [TealTiger](https://github.com/agentguard-ai/tealtiger) — Apache 2.0 deterministic governance engine
- [Strands Hooks Documentation](https://strandsagents.com/docs/user-guide/concepts/agents/hooks/)
- [OWASP Agentic Security Initiatives](https://owasp.org/www-project-agentic-security-initiatives/) — ASI-02 (tool misuse), ASI-03 (access control)

## Disclaimer

This sample is provided for educational and demonstration purposes only. It is not intended for production use without further development, testing, and hardening.

For production deployments, consider:

- Implementing appropriate content filtering and safety measures
- Following security best practices for your deployment environment
- Conducting thorough testing and validation
- Reviewing and adjusting configurations for your specific requirements
