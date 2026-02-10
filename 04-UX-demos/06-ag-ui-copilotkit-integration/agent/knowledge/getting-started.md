# Getting Started with Amazon Bedrock AgentCore

Amazon Bedrock AgentCore Runtime is a secure, serverless runtime purpose-built for deploying and scaling dynamic AI agents. This guide will help you deploy your first agent.

## Prerequisites

Before you begin, ensure you have:

- **AWS Account** with appropriate permissions
- **AWS CLI** configured with credentials
- **Python 3.11+** installed
- **AgentCore CLI** installed (`pip install bedrock-agentcore`)

## Quick Start

### Step 1: Create Your Agent

Create a simple agent using the Strands SDK:

```python
from strands import Agent

agent = Agent(
    model="anthropic.claude-3-haiku-20240307-v1:0",
    system_prompt="You are a helpful assistant."
)
```

### Step 2: Configure for AgentCore

Run the AgentCore CLI to configure your agent:

```bash
agentcore configure -e main.py
```

You'll be prompted for:
- Agent name
- Dependency file (pyproject.toml or requirements.txt)
- Deployment type (Container recommended)
- Execution role (auto-create or provide ARN)

### Step 3: Deploy

Launch your agent to AgentCore Runtime:

```bash
agentcore launch
```

This will:
1. Build a container image
2. Push to Amazon ECR
3. Deploy to AgentCore Runtime
4. Return your runtime endpoint URL

## Verifying Deployment

Test your deployed agent:

```bash
curl -X POST "https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{runtime-id}/invocations" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

## Next Steps

- Learn about [AgentCore Concepts](concepts.md)
- Review [Best Practices](best-practices.md)
- Explore advanced features like Memory and Gateway

## Troubleshooting

### Common Issues

**Container build fails:**
- Ensure all dependencies are in pyproject.toml
- Check Python version compatibility

**Deployment timeout:**
- Verify IAM permissions
- Check ECR repository access

**Runtime errors:**
- Review CloudWatch logs
- Verify environment variables
