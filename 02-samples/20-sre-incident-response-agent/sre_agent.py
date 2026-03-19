"""
SRE Incident Response Agent using Strands Agents SDK

This sample demonstrates a multi-agent SRE system that:
1. Monitors AWS CloudWatch alarms and fetches metrics/logs
2. Performs root cause analysis using a specialized sub-agent
3. Proposes and optionally executes Kubernetes/Helm remediation actions
4. Posts a structured incident report to a Slack channel

Architecture:
  supervisor_agent
    ├── cloudwatch_agent   (AWS metrics, logs, alarm details)
    ├── rca_agent          (root cause analysis reasoning)
    └── remediation_agent  (kubectl / helm dry-run suggestions)
"""

import json
import os
import datetime
from typing import Any

import boto3
from dotenv import load_dotenv
from strands import Agent, tool
from strands.models import BedrockModel

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()  # load variables from .env into os.environ (does not overwrite existing env vars)

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")  # optional
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"

MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0"
)

model = BedrockModel(
    model_id=MODEL_ID,
    region_name=AWS_REGION,
)

# ---------------------------------------------------------------------------
# CloudWatch Tools
# ---------------------------------------------------------------------------


@tool
def list_active_alarms(namespace: str = "") -> str:
    """
    List all CloudWatch alarms currently in ALARM state.

    Args:
        namespace: Optional CloudWatch namespace filter (e.g. 'AWS/ECS', 'AWS/Lambda').
                   If empty, returns alarms from all namespaces.

    Returns:
        JSON string with list of active alarms including name, state, metric, and threshold.
    """
    cw = boto3.client("cloudwatch", region_name=AWS_REGION)
    kwargs: dict[str, Any] = {"StateValue": "ALARM"}

    paginator = cw.get_paginator("describe_alarms")
    alarms = []
    for page in paginator.paginate(**kwargs):
        for alarm in page.get("MetricAlarms", []):
            # Filter by namespace in Python rather than using AlarmNamePrefix,
            # which matches on alarm *name* not namespace and would silently
            # return an empty list when a namespace string is passed.
            if namespace and alarm.get("Namespace", "") != namespace:
                continue
            alarms.append(
                {
                    "name": alarm["AlarmName"],
                    "namespace": alarm.get("Namespace", ""),
                    "metric": alarm.get("MetricName", ""),
                    "threshold": alarm.get("Threshold"),
                    "comparison": alarm.get("ComparisonOperator", ""),
                    "state_reason": alarm.get("StateReason", ""),
                    "updated": str(alarm.get("StateUpdatedTimestamp", "")),
                }
            )
    return json.dumps(alarms, default=str)


@tool
def get_metric_statistics(
        namespace: str,
        metric_name: str,
        dimensions: str,
        period_minutes: int = 30,
) -> str:
    """
    Retrieve CloudWatch metric statistics for the last N minutes.

    Args:
        namespace:      CloudWatch namespace, e.g. 'AWS/ECS' or 'AWS/Lambda'.
        metric_name:    Metric name, e.g. 'CPUUtilization' or 'Errors'.
        dimensions:     JSON string of dimension name/value pairs,
                        e.g. '[{"Name":"ServiceName","Value":"my-svc"}]'.
        period_minutes: How many minutes of history to fetch (default 30).

    Returns:
        JSON string with datapoints (timestamp, average, sum, unit).
    """
    cw = boto3.client("cloudwatch", region_name=AWS_REGION)
    end_time = datetime.datetime.now(datetime.timezone.utc)
    start_time = end_time - datetime.timedelta(minutes=period_minutes)

    try:
        dims = json.loads(dimensions)
    except json.JSONDecodeError:
        dims = []

    response = cw.get_metric_statistics(
        Namespace=namespace,
        MetricName=metric_name,
        Dimensions=dims,
        StartTime=start_time,
        EndTime=end_time,
        Period=60,
        Statistics=["Average", "Sum", "Maximum"],
    )
    datapoints = sorted(
        response.get("Datapoints", []), key=lambda x: x["Timestamp"]
    )
    result = [
        {
            "timestamp": str(dp["Timestamp"]),
            "average": dp.get("Average"),
            "sum": dp.get("Sum"),
            "maximum": dp.get("Maximum"),
            "unit": dp.get("Unit"),
        }
        for dp in datapoints
    ]
    return json.dumps(result, default=str)


@tool
def fetch_log_events(
        log_group: str,
        filter_pattern: str = "ERROR",
        minutes_back: int = 15,
        max_events: int = 50,
) -> str:
    """
    Fetch recent CloudWatch Logs events matching a filter pattern.

    Args:
        log_group:      CloudWatch log group name (e.g. '/ecs/my-service').
        filter_pattern: CloudWatch Logs filter pattern (default 'ERROR').
        minutes_back:   How many minutes of logs to search (default 15).
        max_events:     Maximum number of log events to return (default 50).

    Returns:
        JSON string with matching log events including timestamp and message.
    """
    logs = boto3.client("logs", region_name=AWS_REGION)
    end_time = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
    start_time = end_time - (minutes_back * 60 * 1000)

    try:
        response = logs.filter_log_events(
            logGroupName=log_group,
            startTime=start_time,
            endTime=end_time,
            filterPattern=filter_pattern,
            limit=max_events,
        )
        events = [
            {
                "timestamp": str(
                    datetime.datetime.fromtimestamp(e["timestamp"] / 1000, datetime.timezone.utc)
                ),
                "message": e["message"].strip(),
                "stream": e.get("logStreamName", ""),
            }
            for e in response.get("events", [])
        ]
    except logs.exceptions.ResourceNotFoundException:
        events = [{"error": f"Log group '{log_group}' not found"}]

    return json.dumps(events, default=str)


# ---------------------------------------------------------------------------
# Kubernetes / Helm Remediation Tools
# ---------------------------------------------------------------------------


@tool
def kubectl_get(resource_type: str, namespace: str = "default") -> str:
    """
    Run 'kubectl get <resource_type> -n <namespace>' and return output.
    In DRY_RUN mode returns simulated output without executing real commands.

    Args:
        resource_type: Kubernetes resource type (e.g. 'pods', 'deployments', 'hpa').
        namespace:     Kubernetes namespace (default 'default').

    Returns:
        String output from kubectl or simulated dry-run output.
    """
    if DRY_RUN:
        return (
            f"[DRY-RUN] kubectl get {resource_type} -n {namespace}\n"
            f"NAME                          READY   STATUS    RESTARTS   AGE\n"
            f"my-service-7d9f4b6c8-xk2pq   1/1     Running   3          2d\n"
            f"my-service-7d9f4b6c8-lm8rt   0/1     OOMKilled  1         5m\n"
        )
    import subprocess  # noqa: PLC0415

    result = subprocess.run(
        ["kubectl", "get", resource_type, "-n", namespace, "-o", "wide"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    return result.stdout or result.stderr


@tool
def kubectl_rollout_restart(deployment: str, namespace: str = "default") -> str:
    """
    Restart a Kubernetes deployment with a rolling update.
    In DRY_RUN mode prints the command without executing it.

    Args:
        deployment: Deployment name to restart.
        namespace:  Kubernetes namespace (default 'default').

    Returns:
        Confirmation message or dry-run notice.
    """
    if DRY_RUN:
        return (
            f"[DRY-RUN] kubectl rollout restart deployment/{deployment} "
            f"-n {namespace}\n"
            "This would trigger a rolling restart of all pods in the deployment."
        )
    import subprocess  # noqa: PLC0415

    result = subprocess.run(
        ["kubectl", "rollout", "restart", f"deployment/{deployment}", "-n", namespace],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout or result.stderr


@tool
def helm_rollback(release: str, revision: int = 0, namespace: str = "default") -> str:
    """
    Roll back a Helm release to a previous revision.
    In DRY_RUN mode prints the command without executing it.

    Args:
        release:   Helm release name.
        revision:  Target revision number (0 = previous revision).
        namespace: Kubernetes namespace (default 'default').

    Returns:
        Confirmation message or dry-run notice.
    """
    rev_str = str(revision) if revision > 0 else ""
    if DRY_RUN:
        return (
            f"[DRY-RUN] helm rollback {release} {rev_str} -n {namespace}\n"
            "This would roll the release back to the previous stable revision."
        )
    import subprocess  # noqa: PLC0415

    cmd = ["helm", "rollback", release]
    if revision > 0:
        cmd.append(str(revision))
    cmd += ["-n", namespace]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return result.stdout or result.stderr


@tool
def helm_scale(
        release: str, replicas: int, namespace: str = "default"
) -> str:
    """
    Scale a Helm-managed deployment by patching replica count.
    In DRY_RUN mode prints the command without executing it.

    Args:
        release:   Helm release name (used as deployment name prefix).
        replicas:  Desired number of replicas.
        namespace: Kubernetes namespace (default 'default').

    Returns:
        Confirmation message or dry-run notice.
    """
    if DRY_RUN:
        return (
            f"[DRY-RUN] kubectl scale deployment/{release} "
            f"--replicas={replicas} -n {namespace}\n"
            f"This would scale the deployment to {replicas} replicas."
        )
    import subprocess  # noqa: PLC0415

    result = subprocess.run(
        [
            "kubectl",
            "scale",
            f"deployment/{release}",
            f"--replicas={replicas}",
            "-n",
            namespace,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout or result.stderr


# ---------------------------------------------------------------------------
# Notification Tool
# ---------------------------------------------------------------------------


@tool
def post_incident_report(summary: str, severity: str = "P2") -> str:
    """
    Post a structured incident report. If SLACK_WEBHOOK_URL is set, posts to
    Slack; otherwise prints to stdout.

    Args:
        summary:  Full incident summary in markdown format.
        severity: Incident severity label (P1/P2/P3, default P2).

    Returns:
        Confirmation of where the report was sent.
    """
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC").replace("+00:00", "")
    report = (
        f"*[{severity}] SRE Incident Report — {timestamp}*\n\n{summary}"
    )

    if SLACK_WEBHOOK_URL:
        import urllib.request  # noqa: PLC0415

        payload = json.dumps({"text": report}).encode("utf-8")
        req = urllib.request.Request(
            SLACK_WEBHOOK_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
        return f"Incident report posted to Slack (HTTP {status})."

    print("\n" + "=" * 70)
    print(report)
    print("=" * 70 + "\n")
    return "Incident report printed to stdout (no SLACK_WEBHOOK_URL configured)."


# ---------------------------------------------------------------------------
# Sub-Agents wrapped as Tools (Agents-as-Tools pattern)
# ---------------------------------------------------------------------------

_cloudwatch_agent = Agent(
    model=model,
    system_prompt="""You are a CloudWatch Monitoring specialist.
Your job is to:
1. List any active alarms.
2. Fetch the relevant metric statistics for the alarms you find.
3. Pull recent error log events from the associated log group.
4. Return a concise, structured summary of what the data shows.

Always include timestamps and specific metric values in your summary.
""",
    tools=[list_active_alarms, get_metric_statistics, fetch_log_events],
)

_rca_agent = Agent(
    model=model,
    system_prompt="""You are a senior Site Reliability Engineer performing root cause analysis.
Given alarm data, metrics, and log snippets, your job is to:
1. Identify the most likely root cause(s).
2. Assess the blast radius (which services/users are affected).
3. Rate the severity (P1 critical / P2 high / P3 medium).
4. Propose 2-3 concrete remediation options ranked by risk.

Be precise. Use technical language. Cite specific metric values and log lines.
""",
    tools=[],
)

_remediation_agent = Agent(
    model=model,
    system_prompt="""You are a Kubernetes and Helm operations expert.
Given a root cause analysis, your job is to:
1. Inspect the current state of affected workloads with kubectl.
2. Propose and execute the safest remediation action (rollback, restart, scale).
3. Always prefer reversible actions (rollback > restart > scale).
4. Confirm the action taken or explain why no action was taken.

In DRY_RUN mode, commands are simulated and safe to run.
""",
    tools=[kubectl_get, kubectl_rollout_restart, helm_rollback, helm_scale],
)


@tool
def cloudwatch_agent(task: str) -> str:
    """
    Delegate a CloudWatch monitoring task to the specialist agent.
    Use this to list active alarms, fetch metric statistics, and pull error logs.

    Args:
        task: Natural language description of the monitoring task to perform.

    Returns:
        Structured summary of alarms, metrics, and log events found.
    """
    response = _cloudwatch_agent(task)
    return str(response)


@tool
def rca_agent(context: str) -> str:
    """
    Delegate root cause analysis to the SRE specialist agent.
    Provide alarm data, metrics, and log snippets as context.

    Args:
        context: Full context including alarm details, metric values, and log events.

    Returns:
        Root cause analysis with severity rating and ranked remediation options.
    """
    response = _rca_agent(context)
    return str(response)


@tool
def remediation_agent(instructions: str) -> str:
    """
    Delegate Kubernetes/Helm remediation to the operations specialist agent.
    Use this to inspect workloads and apply rollback, restart, or scaling actions.

    Args:
        instructions: Root cause analysis and remediation instructions.

    Returns:
        Confirmation of actions taken or dry-run command output.
    """
    response = _remediation_agent(instructions)
    return str(response)


# ---------------------------------------------------------------------------
# Supervisor Agent
# ---------------------------------------------------------------------------

supervisor_agent = Agent(
    model=model,
    system_prompt="""You are the SRE Incident Commander orchestrating an incident response.

Follow this workflow:
1. Call cloudwatch_agent to gather all alarm and metric data.
2. Call rca_agent with the gathered data to perform root cause analysis.
3. Call remediation_agent with the RCA findings to inspect workloads and apply a fix.
4. Synthesise findings into a final incident report and post it using the
   post_incident_report tool.

Be decisive. Keep the report concise but complete: include
- What happened (alarm triggered, metric values)
- Why it happened (root cause)
- What was done (remediation action)
- What to watch next (follow-up items)
""",
    tools=[cloudwatch_agent, rca_agent, remediation_agent, post_incident_report],
)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_incident_response(trigger: str = "") -> None:
    """
    Run the SRE incident response workflow.

    Args:
        trigger: Optional natural-language description of the triggering event.
                 If empty, the agent will discover active alarms on its own.
    """
    if not trigger:
        trigger = (
            "There may be active CloudWatch alarms. Please investigate, perform "
            "root cause analysis, apply the appropriate remediation, and post an "
            "incident report."
        )

    print(f"\n Starting SRE Incident Response\n   Trigger: {trigger}\n")
    supervisor_agent(trigger)


if __name__ == "__main__":
    import sys

    user_trigger = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    run_incident_response(user_trigger)