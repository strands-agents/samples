# Getting Started with Amazon Bedrock AgentCore

Amazon Bedrock AgentCore Runtime is a secure, serverless runtime purpose-built for deploying and scaling dynamic AI agents. This guide walks you through scaffolding, testing, and deploying your first agent using the **AgentCore CLI** (`@aws/agentcore`), the currently recommended tool.

## Prerequisites

Before you begin, ensure you have:

- **AWS Account** with appropriate permissions
- **AWS CLI** configured with credentials
- **Node.js 20+** (the CLI itself runs on Node.js)
- **Python 3.10+** (if you're writing a Python agent, e.g. with Strands)
- **uv** for Python agent dependency management ([install](https://docs.astral.sh/uv/getting-started/installation/))
- [Model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html) enabled in Amazon Bedrock for your chosen model (e.g. Anthropic Claude Sonnet 4.6)

## Install the AgentCore CLI

Install globally from npm:

```bash
npm install -g @aws/agentcore
```

> **Upgrading from the old starter toolkit?** If you previously installed `bedrock-agentcore-starter-toolkit` (pip/pipx/uv), uninstall it first. Both CLIs use the `agentcore` command name. The new CLI will show a warning if it detects the old one.

Verify the install:

```bash
agentcore --version
```

## Quick Start

### Step 1: Create a New Project

Launch the interactive wizard:

```bash
agentcore create
```

The wizard prompts you for:

- Project name
- Agent framework (Strands, LangChain/LangGraph, Google ADK, OpenAI Agents)
- Model provider (Amazon Bedrock, Anthropic, Google Gemini, OpenAI)
- Model ID (defaults to a recent Claude Sonnet on Bedrock)
- Whether to enable memory, credentials, evaluators, etc.

It scaffolds a project like this:

```
my-project/
├── agentcore/
│   ├── agentcore.json      # Agent, memory, credentials, eval specs
│   ├── aws-targets.json    # Account and region for deployment
│   └── .env.local          # API keys (gitignored)
└── app/
    └── <AgentName>/
        ├── main.py         # Agent entry point
        ├── pyproject.toml
        └── model/
```

Change into the new directory:

```bash
cd my-project
```

### Step 2: Test Locally

Start a local dev server with hot reload:

```bash
agentcore dev
```

This runs your agent on `http://localhost:8080` so you can iterate quickly without deploying to AWS.

You can also invoke the local agent:

```bash
agentcore invoke '{"prompt": "Hello"}' --local
```

### Step 3: Deploy to AWS

Deploy the agent to AgentCore Runtime:

```bash
agentcore deploy
```

This will:

1. Package your agent
2. Build the container (via AWS CodeBuild by default, so no local Docker is required)
3. Push the image to Amazon ECR
4. Create / update the AgentCore Runtime and endpoint
5. Return the runtime ARN and endpoint URL

### Step 4: Invoke the Deployed Agent

```bash
agentcore invoke '{"prompt": "Hello from AgentCore!"}'
```

The CLI tracks the last session ID automatically, so follow-up calls in the same conversation just work.

## Useful Follow-Up Commands

| Command | Purpose |
|---|---|
| `agentcore status` | Show deployment status, endpoint readiness, VPC config, CloudWatch log paths |
| `agentcore logs` | Stream or search agent runtime logs |
| `agentcore traces list` / `traces get` | Inspect traces for debugging |
| `agentcore add memory` | Add short- or long-term memory to the agent |
| `agentcore add credentials` | Store API keys securely via Secrets Manager |
| `agentcore add evaluator` | Add an LLM-as-a-Judge evaluator |
| `agentcore run eval` | Run an evaluation against recent traces |
| `agentcore destroy` | Tear down all deployed resources for the project |

> After any `add` or `remove`, run `agentcore deploy` again to sync the changes to AWS.

## Verifying Deployment

`agentcore status` gives you a quick health view, or you can invoke the runtime directly via AWS SDKs / HTTPS. Typical verification flow:

```bash
agentcore status
agentcore invoke '{"prompt": "ping"}'
agentcore logs --follow
```

## Next Steps

- Learn about [AgentCore Concepts](concepts.md): Runtime, Memory, Gateway, Identity
- Review [Best Practices](best-practices.md): architecture, security, performance, observability
- Explore advanced capabilities: MCP Gateway for external tools, AgentCore Memory strategies, evaluations, and Policy for guardrails

## Troubleshooting

### Common Issues

**`agentcore` command not found after install:**
- Make sure `npm config get prefix`'s `bin` directory is on your `PATH`
- On macOS/Linux with nvm, re-source your shell or restart the terminal

**Deployment fails with IAM errors:**
- `agentcore deploy` creates an execution role on first run; your AWS credentials need permission to create IAM roles, or you can pass an existing role explicitly (see `agentcore create` options)
- For CodeBuild-based builds, you also need CodeBuild permissions

**Agent times out or errors at runtime:**
- `agentcore logs --follow` shows live CloudWatch logs
- `agentcore traces list` then `agentcore traces get <id>` gives structured traces
- Verify Bedrock model access is enabled in your account's region

**Old CLI conflicts:**
- If the new CLI warns about the old starter toolkit, uninstall it with whichever tool you used: `pip uninstall bedrock-agentcore-starter-toolkit` (or `pipx` / `uv tool`)
