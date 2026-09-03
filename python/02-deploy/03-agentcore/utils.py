"""boto3 helpers for the parts of an AgentCore Runtime deployment that an application owns.

The deploy lifecycle (create project, deploy, remove) runs through the AgentCore CLI directly
in the notebook, and invocation is shown inline there too. These helpers cover the IAM execution
role the agent runs with, looking up a runtime ARN, and verifying that resources are gone after
cleanup.
"""

import json
import time

import boto3


def create_execution_role(agent_name, extra_statements=None):
    """Create an IAM execution role that AgentCore Runtime assumes to run the agent.

    The base permissions are the official AgentCore direct code deployment execution role
    (CloudWatch Logs, X-Ray, CloudWatch metrics, Amazon Bedrock model invocation) plus
    workload identity access. Pass ``extra_statements`` for whatever the agent's own
    business logic needs.

    Args:
        agent_name: Name of the agent (used to construct the role name).
        extra_statements: Optional list of additional IAM policy statements.

    Returns:
        Tuple of (role_arn, role_name).
    """
    iam = boto3.client("iam")
    sts = boto3.client("sts")
    region = boto3.session.Session().region_name
    account_id = sts.get_caller_identity()["Account"]
    role_name = f"agentcore-{agent_name}-role"

    # Trust policy that allows Amazon Bedrock AgentCore to assume this role
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {"aws:SourceAccount": account_id},
                    "ArnLike": {"aws:SourceArn": f"arn:aws:bedrock-agentcore:{region}:{account_id}:*"},
                },
            }
        ],
    }

    statements = [
        # Allow the runtime to create its log group and log streams
        {
            "Effect": "Allow",
            "Action": ["logs:DescribeLogStreams", "logs:CreateLogGroup"],
            "Resource": f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*",
        },
        {
            "Effect": "Allow",
            "Action": ["logs:DescribeLogGroups"],
            "Resource": f"arn:aws:logs:{region}:{account_id}:log-group:*",
        },
        {
            "Effect": "Allow",
            "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
            "Resource": f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*",
        },
        # Allow the runtime to send traces to AWS X-Ray
        {
            "Effect": "Allow",
            "Action": ["xray:PutTraceSegments", "xray:PutTelemetryRecords", "xray:GetSamplingRules", "xray:GetSamplingTargets"],
            "Resource": "*",
        },
        # Allow the runtime to publish metrics to Amazon CloudWatch
        {
            "Effect": "Allow",
            "Action": "cloudwatch:PutMetricData",
            "Resource": "*",
            "Condition": {"StringEquals": {"cloudwatch:namespace": "bedrock-agentcore"}},
        },
        # Allow the agent to invoke Amazon Bedrock foundation models
        {
            "Effect": "Allow",
            "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
            "Resource": ["arn:aws:bedrock:*::foundation-model/*", f"arn:aws:bedrock:{region}:{account_id}:*"],
        },
        # Allow the runtime to retrieve workload identity tokens
        {
            "Effect": "Allow",
            "Action": ["bedrock-agentcore:GetWorkloadAccessToken*"],
            "Resource": f"arn:aws:bedrock-agentcore:{region}:{account_id}:workload-identity-directory/*",
        },
    ]
    statements.extend(extra_statements or [])
    permissions_policy = {"Version": "2012-10-17", "Statement": statements}

    # Create the role if it doesn't exist
    try:
        iam.create_role(RoleName=role_name, AssumeRolePolicyDocument=json.dumps(trust_policy))
        print(f"Created role: {role_name}")
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"Role exists: {role_name}")

    # Attach the permissions policy to the role
    iam.put_role_policy(RoleName=role_name, PolicyName="AgentCorePolicy", PolicyDocument=json.dumps(permissions_policy))

    # Wait for IAM role to propagate
    time.sleep(10)

    return f"arn:aws:iam::{account_id}:role/{role_name}", role_name


def delete_execution_role(agent_name):
    """Delete the IAM execution role and its inline policies.

    A role that is already gone is reported, not treated as an error. Any other failure raises.

    Args:
        agent_name: Name of the agent (used to construct the role name).
    """
    iam = boto3.client("iam")
    role_name = f"agentcore-{agent_name}-role"

    try:
        for policy_name in iam.list_role_policies(RoleName=role_name)["PolicyNames"]:
            iam.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
        iam.delete_role(RoleName=role_name)
        print(f"Deleted role: {role_name}")
    except iam.exceptions.NoSuchEntityException:
        print(f"Role already deleted: {role_name}")


def _list_runtime_names_to_arns():
    """Return {agentRuntimeName: agentRuntimeArn} for every runtime in the account and Region."""
    control = boto3.client("bedrock-agentcore-control")
    runtimes = {}
    kwargs = {}
    while True:
        page = control.list_agent_runtimes(**kwargs)
        runtimes.update({r["agentRuntimeName"]: r["agentRuntimeArn"] for r in page["agentRuntimes"]})
        if "nextToken" not in page:
            return runtimes
        kwargs["nextToken"] = page["nextToken"]


def get_runtime_arn(project_name, agent_name):
    """Look up a deployed agent's runtime ARN.

    The AgentCore CLI names each runtime ``<project>_<agent>``. An application typically reads
    the ARN from configuration; here it is looked up by name so the notebook has no hardcoded ARNs.

    Args:
        project_name: The CLI project name.
        agent_name: The agent name as configured in the project.

    Returns:
        The AgentCore Runtime ARN.

    Raises:
        RuntimeError: No runtime with that name exists.
    """
    runtime_name = f"{project_name}_{agent_name}"
    arn = _list_runtime_names_to_arns().get(runtime_name)
    if arn is None:
        raise RuntimeError(f"No AgentCore Runtime named {runtime_name} found. Has the deploy finished?")
    print(arn)
    return arn


def assert_runtimes_absent(project_name, *agent_names):
    """Verify that no AgentCore Runtime remains for the given agents.

    Raises if any still exist, so a cleanup that silently did nothing cannot pass.

    Args:
        project_name: The CLI project name.
        *agent_names: Agent names as configured in the project.
    """
    expected = {f"{project_name}_{name}" for name in agent_names}
    survivors = sorted(expected & set(_list_runtime_names_to_arns()))
    if survivors:
        raise RuntimeError(f"Runtimes still exist: {survivors}")
    print(f"Verified: no runtime exists for {sorted(expected)}")


def assert_stack_absent(stack_name):
    """Verify that the project's CloudFormation stack has been deleted.

    Args:
        stack_name: The stack name the AgentCore CLI deployed.
    """
    cfn = boto3.client("cloudformation")
    try:
        status = cfn.describe_stacks(StackName=stack_name)["Stacks"][0]["StackStatus"]
    except cfn.exceptions.ClientError as e:
        if "does not exist" in str(e):
            print(f"Verified: stack {stack_name} is deleted")
            return
        raise
    raise RuntimeError(f"Stack {stack_name} still exists with status {status}")
