"""Utility functions for Amazon Bedrock AgentCore deployment."""

import boto3
import json
import time


def create_execution_role(agent_name):
    """Create an IAM execution role with all permissions required for the restaurant agent.

    Args:
        agent_name: Name of the agent (used to construct role name)

    Returns:
        Tuple of (role_arn, role_name)
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
                    "ArnLike": {"aws:SourceArn": f"arn:aws:bedrock-agentcore:{region}:{account_id}:*"}
                }
            }
        ]
    }

    # Permissions policy for AgentCore runtime execution
    permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [
            # Allow the runtime to invoke Amazon Bedrock foundation models
            {
                "Effect": "Allow",
                "Action": ["bedrock:InvokeModel*"],
                "Resource": "*"
            },
            # Allow the runtime to pull container images from Amazon ECR
            {
                "Effect": "Allow",
                "Action": ["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer", "ecr:GetAuthorizationToken"],
                "Resource": "*"
            },
            # Allow the runtime to write logs to Amazon CloudWatch Logs
            {
                "Effect": "Allow",
                "Action": ["logs:*"],
                "Resource": f"arn:aws:logs:{region}:{account_id}:log-group:*"
            },
            # Allow the runtime to send traces to AWS X-Ray
            {
                "Effect": "Allow",
                "Action": ["xray:Put*", "xray:GetSampling*"],
                "Resource": "*"
            },
            # Allow the runtime to publish metrics to Amazon CloudWatch
            {
                "Effect": "Allow",
                "Action": "cloudwatch:PutMetricData",
                "Resource": "*"
            },
            # Allow the runtime to retrieve workload identity tokens
            {
                "Effect": "Allow",
                "Action": ["bedrock-agentcore:GetWorkloadAccessToken*"],
                "Resource": f"arn:aws:bedrock-agentcore:{region}:{account_id}:workload-identity-directory/*"
            },
            # Allow the agent to query Amazon Bedrock Knowledge Bases
            {
                "Effect": "Allow",
                "Action": ["bedrock:Retrieve*"],
                "Resource": f"arn:aws:bedrock:{region}:{account_id}:knowledge-base/*"
            },
            # Allow the agent to read and write to Amazon DynamoDB tables
            {
                "Effect": "Allow",
                "Action": ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:DeleteItem", "dynamodb:Scan", "dynamodb:Query"],
                "Resource": f"arn:aws:dynamodb:{region}:{account_id}:table/*"
            },
            # Allow the agent to read parameters from AWS Systems Manager Parameter Store
            {
                "Effect": "Allow",
                "Action": ["ssm:GetParameter*"],
                "Resource": f"arn:aws:ssm:{region}:{account_id}:parameter/*"
            }
        ]
    }

    # Create the role if it doesn't exist
    try:
        iam.create_role(RoleName=role_name, AssumeRolePolicyDocument=json.dumps(trust_policy))
        print(f"Created role: {role_name}")
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"Role exists: {role_name}")

    # Attach the permissions policy to the role
    iam.put_role_policy(RoleName=role_name, PolicyName="AgentCorePolicy",
                        PolicyDocument=json.dumps(permissions_policy))

    # Wait for IAM role to propagate across AWS regions
    time.sleep(10)

    return f"arn:aws:iam::{account_id}:role/{role_name}", role_name


def delete_execution_role(agent_name):
    """Delete the IAM execution role and its attached policies.

    Args:
        agent_name: Name of the agent (used to construct role name)
    """
    iam = boto3.client("iam")
    role_name = f"agentcore-{agent_name}-role"

    try:
        # Delete all inline policies attached to the role
        for policy_name in iam.list_role_policies(RoleName=role_name).get("PolicyNames", []):
            iam.delete_role_policy(RoleName=role_name, PolicyName=policy_name)

        # Delete the role
        iam.delete_role(RoleName=role_name)
        print(f"Deleted role: {role_name}")
    except Exception:
        pass
