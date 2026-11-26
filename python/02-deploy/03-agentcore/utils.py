"""boto3 helpers for the parts of an AgentCore Runtime deployment that an application owns.

The deploy lifecycle (create project, deploy, remove) runs through the AgentCore CLI directly
in the notebook, and invocation is shown inline there too. These helpers create and delete the
IAM execution role that an agent runs with.
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
