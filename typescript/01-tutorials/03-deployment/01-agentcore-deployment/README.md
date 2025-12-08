# Deploying Strands Agents to Amazon Bedrock AgentCore Runtime

## Overview

In this tutorial, we will guide you through deploying a Strands Agent to Amazon Bedrock AgentCore Runtime for production workloads.

![Agent Architecture](images/architecture_runtime.png)

| Feature | Description |
|---------|-------------|
| Deployment target | Amazon Bedrock AgentCore Runtime |
| Agent type | Single agent with Express server |
| Model | Claude 3.5 Haiku via Amazon Bedrock |

## Prerequisites

- Node.js 20.x or later
- Docker with buildx support
- AWS CLI configured with appropriate permissions
- AWS account with AgentCore access

## Running Locally

```bash
cd typescript/01-tutorials/03-deployment/01-agentcore-deployment
npm install
npm run dev
```

Test the agent:
```bash
curl http://localhost:8080/ping
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"input": {"prompt": "What is the weather?"}}'
```

## Deploying to AgentCore

### Deploy Infrastructure

```bash
aws cloudformation deploy \
  --template-file prerequisites.yaml \
  --stack-name agentcore-prerequisites \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### Build and Push Docker Image

```bash
REPO_URI=$(aws cloudformation describe-stacks \
  --stack-name agentcore-prerequisites \
  --query 'Stacks[0].Outputs[?OutputKey==`RepositoryUri`].OutputValue' \
  --output text)

aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ${REPO_URI%%/*}

docker buildx build --platform linux/arm64 -t $REPO_URI --push .
```

### Create AgentCore Runtime

```bash
npm run deploy
```

### Invoke Deployed Agent

```bash
AGENT_RUNTIME_ARN=<arn-from-deploy> npm run invoke "What is the weather?"
```

## Key Concepts

### AgentCore Runtime Service Contract

AgentCore Runtime requires a containerized application exposing two HTTP endpoints: `/ping` for status tracking and `/invocations` for processing requests:

```typescript
app.get('/ping', (_req, res) => {
  res.json({ status: 'Healthy' });
});

app.post('/invocations', async (req, res) => {
  const prompt = req.body.input?.prompt;
  const result = await agent.invoke(prompt);
  res.type('text/plain').send(result.toString());
});
```

### Creating an AgentCore Runtime

Use the AWS SDK to create an AgentCore Runtime that references your container image:

```typescript
const command = new CreateAgentRuntimeCommand({
  agentRuntimeName: AGENT_NAME,
  agentRuntimeArtifact: {
    containerConfiguration: { containerUri: `${repositoryUri}:latest` }
  },
  networkConfiguration: { networkMode: 'PUBLIC' },
  roleArn
});
```

### Invoking the AgentCore Runtime

Send requests to the deployed agent using the InvokeAgentRuntime API:

```typescript
const command = new InvokeAgentRuntimeCommand({
  agentRuntimeArn: AGENT_RUNTIME_ARN,
  runtimeSessionId: sessionId,
  payload: new TextEncoder().encode(prompt),
  qualifier: 'DEFAULT'
});
```

## Project Structure

```
├── Dockerfile            # Container image for AgentCore
├── prerequisites.yaml    # CloudFormation template (IAM role, ECR repo)
├── package.json
├── tsconfig.json
└── src/
    ├── agent.ts          # Express server with Strands Agent
    ├── deploy-agent.ts   # AgentCore deployment script
    └── invoke-agent.ts   # Remote invocation script
```

## Cleanup

```bash
aws bedrock-agentcore-control delete-agent-runtime \
  --agent-runtime-id <runtime-id> --region us-east-1

aws cloudformation delete-stack \
  --stack-name agentcore-prerequisites --region us-east-1
```

## Additional Resources

- [Strands Agents Documentation](https://strandsagents.com/latest/)
- [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/)
- [AgentCore Runtime HTTP Protocol Contract](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-http-protocol-contract.html)
