# Production Deployment Patterns for Strands Agents

This tutorial walks through deploying Strands Agents to production on AWS. You'll learn how to choose the right compute service, containerize your agent, configure infrastructure with CDK, and apply production best practices for security, performance, and observability.


## Tutorial Details

| Information            | Details                                                                 |
|------------------------|-------------------------------------------------------------------------|
| **Strands Features**   | `Agent`, `stream_async`, `BedrockModel`, `SlidingWindowConversationManager` |
| **Agent Pattern**      | Single agent deployed as an HTTP service                                |
| **Tools**              | `http_request` (community tool), custom tools                           |
| **Model**              | Claude Sonnet 4 on Amazon Bedrock                                       |

## What You'll Learn

The tutorial is split into three notebooks covering the full deployment journey:

1. [**01_local_agent_to_http_service.ipynb**](./01_local_agent_to_http_service.ipynb) — Transform a local Strands agent into an HTTP service using FastAPI, add streaming support with `stream_async`, containerize with Docker, and test locally.
2. [**02_deploy_to_aws.ipynb**](./02_deploy_to_aws.ipynb) — Deploy your containerized agent to AWS using two patterns: Lambda (serverless, short-lived) and Fargate (containers, streaming). Includes IAM configuration and end-to-end testing.
3. [**03_production_best_practices.ipynb**](./03_production_best_practices.ipynb) — Harden your deployment with production configuration: conversation management, error handling, security (least-privilege IAM, input validation), observability, and cost optimization.

## Key Concepts

- **Serverless vs. Container deployment**: Lambda for short-lived requests; Fargate/EKS for streaming and long-running agents
- **Streaming responses**: Using `stream_async` with FastAPI `StreamingResponse` for real-time output
- **Production hardening**: Conversation management, error handling, security, and observability

## Prerequisites

- Python 3.10 or later
- AWS account with [Amazon Bedrock](https://aws.amazon.com/bedrock/) model access (Claude Sonnet 4)
- AWS CLI configured (`aws configure`)
- Docker or Podman installed (for containerization notebooks)
- Node.js 18+ (for CDK deployment in Notebook 02)
- Basic familiarity with Strands Agents ([01-first-agent](../01-first-agent/))

## Tutorial Structure

```
20-production-deployment-patterns/
├── README.md
├── requirements.txt
├── 01_local_agent_to_http_service.ipynb
├── 02_deploy_to_aws.ipynb
└── 03_production_best_practices.ipynb
```

| Notebook | Description |
|----------|-------------|
| [01_local_agent_to_http_service.ipynb](./01_local_agent_to_http_service.ipynb) | From local agent to containerized HTTP service |
| [02_deploy_to_aws.ipynb](./02_deploy_to_aws.ipynb) | Deploy to Lambda and Fargate |
| [03_production_best_practices.ipynb](./03_production_best_practices.ipynb) | Security, performance, observability, and cost |

## Getting Started

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify AWS credentials:**
   ```bash
   aws sts get-caller-identity
   ```

3. **Run the notebooks in order** — each builds on concepts from the previous one.

## Deployment Decision Guide

| Criteria | Lambda | Fargate |
|----------|--------|---------|
| **Best for** | Short-lived requests, batch processing | Interactive apps, streaming |
| **Streaming** | ❌ Not supported | ✅ Full streaming |
| **Cold start** | ~2-5s | None (always running) |
| **Max duration** | 15 minutes | Unlimited |
| **Scaling** | Automatic (per-request) | Task-based auto-scaling |
| **Infrastructure** | Minimal (serverless) | VPC, ECS cluster |
| **Cost model** | Per-invocation | Per-hour (tasks running) |

> **See also:** For managed runtime with session isolation, see [Bedrock AgentCore](https://strandsagents.com/docs/user-guide/deploy/deploy_to_bedrock_agentcore/).

## Cleanup

Each notebook includes cleanup cells. Resources are deleted immediately after testing.

## Additional Resources

- [Strands Agents Deployment Docs](https://strandsagents.com/docs/user-guide/deploy/operating-agents-in-production/)
- [Deploy to Lambda](https://strandsagents.com/docs/user-guide/deploy/deploy_to_aws_lambda/)
- [Deploy to Fargate](https://strandsagents.com/docs/user-guide/deploy/deploy_to_aws_fargate/)
- [Deploy to Bedrock AgentCore](https://strandsagents.com/docs/user-guide/deploy/deploy_to_bedrock_agentcore/)
- [Deploy to EKS](https://strandsagents.com/docs/user-guide/deploy/deploy_to_amazon_eks/)
- [Deploy to EC2](https://strandsagents.com/docs/user-guide/deploy/deploy_to_amazon_ec2/)

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `AccessDeniedException` on Bedrock | Missing IAM permissions | Add `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` to task/function role |
| Lambda timeout | Agent response exceeds 30s default | Increase `timeout` in CDK or simplify agent tools |
| Container health check failing | App not listening on expected port | Verify `EXPOSE` in Dockerfile matches ALB target group port |
| `ModuleNotFoundError` in Lambda | Dependencies not in layer | Rebuild layer with correct architecture (`manylinux2014_aarch64` for ARM64) |
| Streaming not working on Lambda | Lambda doesn't support response streaming natively | Use Fargate for streaming |

## Next Steps

- Add [guardrails](../05-guardrails/) for input/output filtering in production
- Implement [session management](../17-conversation-management/) for multi-turn conversations
- Set up [observability](../08-observability/) with CloudWatch and tracing
- Explore [A2A protocol](https://strandsagents.com/docs/user-guide/concepts/multi-agent/agent-to-agent/) for multi-agent deployments
