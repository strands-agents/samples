# Scheduled Agents — EventBridge Scheduler + AgentCore

Invoke a [Strands Agents](https://github.com/strands-agents/sdk-python) agent running on [Bedrock AgentCore](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html) on a recurring schedule using **Amazon EventBridge Scheduler**.

## Architecture

```
EventBridge Scheduler ──▶ EventBridge Bus ──▶ Rule + InputTransformer ──▶ API Destination ──▶ AgentCore Runtime
                                                                              │
                                                                         Cognito OAuth
                                                                       (client_credentials)
```

1. **EventBridge Scheduler** fires on a cron/rate expression and puts an event on a custom EventBridge bus
2. A **Rule** matches events from `scheduler.agentcore` with detail-type `ScheduledAgentInvocation`
3. An **InputTransformer** extracts `$.detail.prompt` into `{"prompt": "<value>"}`
4. An **EventBridge Connection** acquires a Cognito OAuth token via `client_credentials`
5. An **API Destination** POSTs to the AgentCore `/invocations` endpoint with `Authorization: Bearer <jwt>`
6. **AgentCore** validates the JWT and runs the Strands agent

> **Why the extra hop?** EventBridge Scheduler can't target API Destinations directly.
> Scheduler puts an event on a bus, then a Rule routes it to the API Destination.

## Prerequisites

- AWS CLI v2, SAM CLI, Docker (with buildx)
- A Bedrock AgentCore–enabled AWS account

## Project Structure

```
scheduling/
├── agent/
│   ├── agent.py            # Strands agent with get_current_time tool
│   ├── Dockerfile
│   └── requirements.txt
├── deploy.sh               # Full deployment script (7 steps)
├── template.yaml           # SAM template (Cognito, EventBridge bus, DLQ)
└── README.md
```

## Deploy

```bash
# Defaults: rate(1 hour), us-east-1
./deploy.sh

# Custom schedule and region
SCHEDULE_EXPR="cron(0 9 * * ? *)" AWS_REGION=us-west-2 ./deploy.sh
```

The deploy script handles everything in 7 steps:
1. Creates an ECR repository
2. Builds and pushes the agent container (ARM64)
3. Creates the AgentCore execution IAM role
4. Creates the AgentCore Runtime
5. Deploys the SAM stack (Cognito + EventBridge bus + DLQ)
6. Wires up the EventBridge Connection, API Destination, and Rule
7. Creates the EventBridge Schedule

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `STACK_NAME` | `scheduled-agentcore` | CloudFormation stack name |
| `AGENT_NAME` | `scheduled_agentcore_agent` | AgentCore runtime name |
| `AWS_REGION` | `us-east-1` | AWS region |
| `SCHEDULE_EXPR` | `rate(1 hour)` | EventBridge schedule expression |

## Post-Deploy

After deployment, configure the AgentCore JWT authorizer with the Cognito values printed at the end of the deploy script output.

## Test Manually

```bash
aws events put-events --entries '[{
  "EventBusName": "scheduled-agentcore-bus",
  "Source": "scheduler.agentcore",
  "DetailType": "ScheduledAgentInvocation",
  "Detail": "{\"prompt\": \"Hello from manual test!\"}"
}]' --region us-east-1
```

## Cleanup

```bash
STACK_NAME=scheduled-agentcore
REGION=us-east-1

aws scheduler delete-schedule --name ${STACK_NAME}-schedule --region ${REGION}
aws events delete-connection --name ${STACK_NAME}-connection --region ${REGION}
aws cloudformation delete-stack --stack-name ${STACK_NAME} --region ${REGION}
```
