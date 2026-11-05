# Pentest Findings Triage with Darkmoon and the Model Context Protocol

A Strands agent that reads the results of [Darkmoon](https://github.com/ASCIT31/Dark-Moon) autonomous pentest campaigns through the `@darkmoon_ai/mcp-server` MCP server and writes a prioritized triage brief for an engineering team.

## Overview

Darkmoon is an open source (GPL-3.0) autonomous AI penetration testing platform. Its MCP server exposes four tools, and this sample shows how to wire them into a Strands agent with a deliberately narrow blast radius: the agent can only read results, while launching a pentest is a separate command that is allowlisted and needs a typed confirmation.

> **Requires Darkmoon Pro.** The engine and CLI are open source, but `@darkmoon_ai/mcp-server` talks to the Darkmoon Dashboard API, which is part of Darkmoon Pro and always self-hosted. It does not work against the open source CLI alone. Without Pro, consume the CLI's SARIF/JSON output or the [GitHub Action](https://github.com/ASCIT31/darkmoon-action) instead.

### Sample Details

| Information            | Details                                                                 |
|------------------------|-------------------------------------------------------------------------|
| **Agent Architecture** | Single-agent                                                            |
| **Native Tools**       | None                                                                    |
| **Custom Tools**       | None                                                                    |
| **MCP Servers**        | [`@darkmoon_ai/mcp-server`](https://www.npmjs.com/package/@darkmoon_ai/mcp-server) (stdio) |
| **Use Case Vertical**  | Application security                                                    |
| **Complexity**         | Basic                                                                   |
| **Model Provider**     | Amazon Bedrock                                                          |
| **SDK Used**           | Strands Agents SDK                                                      |

### Darkmoon MCP Tools

| Tool             | Description                                                       | Exposed to the agent |
|------------------|-------------------------------------------------------------------|----------------------|
| `list_campaigns` | List campaigns visible to the dashboard user (read only)          | Yes                  |
| `get_findings`   | Findings and severity statistics for one campaign (read only)     | Yes                  |
| `get_run_status` | `running`, `completed`, `error` or `unknown` for a run (read only) | Yes                  |
| `run_pentest`    | Start an autonomous pentest against one authorized target         | No, `scan` command only |

### Key Features

- Uses `tool_filters={"allowed": [...]}` on `MCPClient` so the model is only ever given the read-only tools
- Launching a pentest is outside the model: a `DARKMOON_ALLOWED_TARGETS` allowlist (exact host or `*.wildcard`) and a typed confirmation of the target
- Findings are treated as untrusted data in the system prompt, and the agent reports Darkmoon's remediation text verbatim instead of generating fixes

## Prerequisites

1. **Python 3.10+**
2. **[uv](https://docs.astral.sh/uv/getting-started/installation/)** (or pip) for dependency management
3. **Node.js 18+**, because the MCP server is started with `npx`
4. **AWS credentials** configured, with [model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html) enabled for Anthropic Claude Sonnet 4.5 in Amazon Bedrock
5. **A self-hosted Darkmoon Pro instance** and a dashboard user (or a pre-issued token)

Only run pentests against systems you own or are explicitly authorized in writing to test.

## Setup

1. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your Darkmoon base URL, credentials and allowed targets
   ```

2. **Install dependencies:**
   ```bash
   uv venv
   uv pip install -r requirements.txt
   ```

## Usage

**Triage the most recent completed campaign:**
```bash
uv run findings_triage.py
```

**Triage a specific campaign** (ids come from `list_campaigns`, for example `camp_20260922_abc123`):
```bash
uv run findings_triage.py camp_20260922_abc123
```

**Launch a pentest** (human-gated, never callable by the model):
```bash
uv run findings_triage.py scan staging.example.com
```
The command refuses any target outside `DARKMOON_ALLOWED_TARGETS`, asks you to retype the target, then calls `run_pentest` and prints the returned `run_id`. A run can take a long time; once it has completed, triage its campaign with the first command.

## Configuration

| Variable                              | Description                                                         |
|---------------------------------------|---------------------------------------------------------------------|
| `DARKMOON_BASE_URL`                   | Base URL of your Darkmoon Pro Dashboard API (required)              |
| `DARKMOON_TOKEN`                      | Pre-issued JWT, as an alternative to username and password          |
| `DARKMOON_USERNAME`, `DARKMOON_PASSWORD` | Dashboard credentials                                            |
| `DARKMOON_ALLOWED_TARGETS`            | Comma separated hosts or `*.wildcards` the `scan` command may target |
| `AWS_REGION`                          | Bedrock region, defaults to `us-west-2`                             |

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `DARKMOON_BASE_URL is required` | Variable missing from `.env` | Set the URL of your self-hosted Darkmoon Pro instance |
| `Darkmoon authentication failed` | Wrong token or credentials | Check `DARKMOON_TOKEN` or `DARKMOON_USERNAME`/`DARKMOON_PASSWORD` |
| `Could not reach the Darkmoon Dashboard API` | Instance unreachable from this machine | Check the URL, VPN and TLS certificate |
| `Refusing to scan ...: not in DARKMOON_ALLOWED_TARGETS` | Target is outside the allowlist | Add the host only if you are authorized to test it |

## Additional Resources

- [Darkmoon on GitHub](https://github.com/ASCIT31/Dark-Moon)
- [`@darkmoon_ai/mcp-server` on npm](https://www.npmjs.com/package/@darkmoon_ai/mcp-server)
- [Strands Agents MCP tools documentation](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/mcp-tools/)

## Disclaimer

This sample is provided for educational and demonstration purposes only. It is not intended for production use without further development, testing, and hardening. Pentest findings can include false positives and must be reviewed by a qualified human before any action is taken.
