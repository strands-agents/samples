# SRE Incident Response Agent

A multi-agent SRE incident response system that automatically detects AWS CloudWatch alarms, performs AI-powered root cause analysis, applies Kubernetes/Helm remediations (rollback, restart, scale), and posts structured incident reports to Slack. Demonstrates the multi-agent supervisor pattern with specialist sub-agents for monitoring, RCA, and remediation. Safe by default with dry-run mode. Compatible with OpenShift via `oc` CLI.

---

## Architecture

```
supervisor_agent
    ├── cloudwatch_agent   → list alarms · fetch metrics · pull error logs
    ├── rca_agent          → identify root cause · rate severity · rank fixes
    └── remediation_agent  → inspect k8s workloads · rollback / restart / scale
```

The **supervisor** acts as an Incident Commander. It delegates work to three
specialist sub-agents and then synthesises their findings into a final report.

---

## Features

| Capability | Details |
|---|---|
| **Alarm discovery** | Polls CloudWatch for all active alarms |
| **Metric analysis** | Fetches last 30 min of relevant metric statistics |
| **Log triage** | Pulls error log events from CloudWatch Logs |
| **Root cause analysis** | Reasoning-based RCA with severity scoring (P1/P2/P3) |
| **K8s remediation** | `kubectl get`, rollout restart, Helm rollback, scale |
| **Incident report** | Posts to Slack webhook or prints to stdout |
| **Dry-run safe** | All kubectl/helm commands are simulated by default (`DRY_RUN=true`) |

---

## Prerequisites

- Python 3.11+
- AWS credentials configured (`aws configure` or IAM role)
- Amazon Bedrock access enabled for Claude Sonnet in your region
  ([enable model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html))
- `kubectl` installed and configured (for real remediation; not needed in dry-run)
- `helm` v3 installed (for real Helm rollbacks; not needed in dry-run)

---

## Setup

```bash
# 1. Clone the strands-agents/samples repository
git clone https://github.com/strands-agents/samples.git
cd samples/02-samples/sre-incident-response-agent

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your settings
```

---

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
# AWS settings
AWS_REGION=us-east-1

# Bedrock model (default: Claude Sonnet 4)
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0

# Safety: set to false only when you want live kubectl/helm execution
DRY_RUN=true

# Optional: Slack incoming webhook for incident reports
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## Running the Agent

### Automatic discovery (recommended)

Let the agent discover active alarms on its own:

```bash
python sre_agent.py
```

### Targeted investigation

Provide a specific trigger for faster focus:

```bash
python sre_agent.py "High CPU alarm fired on ECS service my-api in prod namespace"
```

### Example output

```
🚨 Starting SRE Incident Response
   Trigger: High CPU alarm fired on ECS service my-api in prod namespace

[cloudwatch_agent] Fetching active alarms...
  ✓ Found alarm: my-api-HighCPU (CPUUtilization > 85% for 5m)
  ✓ Metric stats: avg 91.3%, max 97.8% over last 30 min
  ✓ Log events: 14 OOMKilled events in /ecs/my-api

[rca_agent] Performing root cause analysis...
  Root cause: Memory leak causing CPU spike as GC thrashes
  Severity: P2 — single service, <5% of users affected
  Recommended fix: Rolling restart to clear heap; monitor for recurrence

[remediation_agent] Applying remediation...
  [DRY-RUN] kubectl rollout restart deployment/my-api -n prod

======================================================================
*[P2] SRE Incident Report — 2025-10-14 09:31 UTC*

**What happened:** CloudWatch alarm `my-api-HighCPU` fired at 09:18 UTC.
CPU utilisation reached 97.8% (threshold: 85%). 14 OOMKilled events detected
in the last 15 minutes in `/ecs/my-api`.

**Root cause:** Memory leak in application heap leading to aggressive GC,
causing CPU saturation. Likely introduced in the last deployment.

**Remediation:** Rolling restart of `deployment/my-api` in namespace `prod`
initiated. All pods will be replaced with fresh instances.

**Follow-up:**
- Monitor CPUUtilization for next 30 min
- Review recent commits for memory allocation changes
- Consider setting memory limits in the Helm chart
======================================================================
```

---

## How it works — Strands SDK concepts demonstrated

| Concept | Where |
|---|---|
| `@tool` decorator | All CloudWatch / kubectl / Helm functions |
| `Agent(agents=[...])` | Supervisor delegates to specialist sub-agents |
| `BedrockModel` | Configurable model provider |
| Multi-agent supervisor pattern | `supervisor_agent` orchestrates 3 sub-agents |
| Tool docstrings as LLM guidance | Every `@tool` has a detailed docstring |

---

## IAM Permissions required

The IAM role or user running this agent needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:DescribeAlarms",
        "cloudwatch:GetMetricStatistics",
        "logs:FilterLogEvents",
        "logs:DescribeLogGroups"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Extending this sample

| Extension idea | How |
|---|---|
| PagerDuty integration | Add a `create_pagerduty_incident` tool |
| GitHub issue creation | Add a `create_github_issue` tool for post-mortems |
| Auto-scaling policies | Add an `update_asg_capacity` tool |
| OpenShift / OKD support | Swap `kubectl` for `oc` commands in remediation tools |
| Custom LLM | Change `BedrockModel` to `AnthropicModel` or `OllamaModel` |

---

## Security note

All `kubectl` and `helm` commands run in **dry-run mode by default**
(`DRY_RUN=true`). Set `DRY_RUN=false` only in environments where you have
tested the agent and trust its remediation decisions. Always apply the
principle of least privilege to the AWS IAM role and Kubernetes RBAC role
used by this agent.

---

## License

Apache License 2.0 — see the [LICENSE](../../LICENSE) file for details.
