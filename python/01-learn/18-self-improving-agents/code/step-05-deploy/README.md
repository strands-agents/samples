# Step 5 - Deploy to Amazon Bedrock AgentCore Runtime

The final step: take the agent off your laptop and run it in AWS, using
the official **[@aws/agentcore](https://github.com/aws/agentcore-cli) CLI**.

## Prerequisites

### 1. Node.js 20+ and the AgentCore CLI

The new AgentCore CLI is an npm package. You need **Node 20 or higher**.

```bash
# (if Node ≥20 is not already available)
nvm install 20 && nvm use 20

# install the CLI
npm install -g @aws/agentcore

# verify
agentcore --version      # → 0.13.0+
```

> If your Node is older than 20, use `nvm install 20 && nvm use 20`
> from a terminal before running `deploy.sh`.

### 2. Python deps and AgentCore Memory ID

```bash
pip install -r requirements.txt
export BEDROCK_AGENTCORE_MEMORY_ID=<your memory id>   # from step-03
```

## Deploy in one command

```bash
./deploy.sh
```

`deploy.sh` idempotently:

1. Runs `agentcore create` to scaffold a `Aim308Deploy/` project (CDK-based)
2. Runs `agentcore add agent --type byo` pointing at this directory's `agent.py`
3. Writes `AWS_REGION` + `BEDROCK_AGENTCORE_MEMORY_ID` into `Aim308Deploy/agentcore/.env.local`
4. Installs CDK deps and runs `agentcore deploy -y`

When it finishes, you'll see the runtime ARN and a ready-to-use `agentcore invoke` command.

## Local dev (faster iteration)

Instead of deploying to AWS for every change, use the CLI's built-in dev server:

```bash
cd Aim308Deploy       # the project created by deploy.sh
agentcore dev          # opens an interactive TUI against your local agent
```

Or run one-shot non-interactive:

```bash
agentcore dev "hello, who are you?"
```

## Invoke your deployed agent

Via the CLI:

```bash
cd Aim308Deploy
agentcore invoke "what can you do?"
agentcore invoke --session-id demo123 "remember I prefer python"
agentcore invoke --session-id demo123 "what do you remember?"
```

Via Python from anywhere (boto3):

```bash
export AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:...:runtime/aim308_research_agent-XYZ
python invoke.py "tell me about yourself"
```

## Observability

```bash
cd Aim308Deploy

agentcore status       # deployment state, ARNs
agentcore logs         # CloudWatch logs (streamed)
agentcore traces list  # recent traces
```

## Cleanup

```bash
cd Aim308Deploy
agentcore remove agent --name aim308_research_agent
agentcore deploy -y    # CDK destroys removed resources
```

Congratulations 🎉 You've built and deployed a self-improving autonomous agent.
