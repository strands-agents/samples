"""IAM role management for Amazon Bedrock AgentCore runtime deployments.

Provides functions to create and delete IAM execution roles with permissions
required for Amazon Bedrock AgentCore runtime. Supports extensible permission
model for agent-specific requirements (e.g., Amazon DynamoDB access for Order Agent).

Key features:
- Trust policy with cross-account protection conditions
- Base permissions for ECR, CloudWatch Logs, AWS X-Ray, Amazon Bedrock
- Extensible additional permissions via function parameters
- Automatic IAM propagation delay handling
"""

import json
import logging
import time
import boto3

logger = logging.getLogger(__name__)

# SSM path prefix for this project
SSM_PATH_PREFIX = "/ecommerce-assistant/*"


def create_agentcore_role(
    role_name: str,
    account_id: str,
    region: str,
    additional_ssm_paths: list[str] | None = None,
    additional_permissions: list[dict] | None = None,
) -> str:
    """Create IAM execution role for Amazon Bedrock AgentCore runtime.

    Creates IAM role with trust policy and permissions required for Amazon Bedrock
    AgentCore to run agent containers. Trust policy allows AgentCore service to
    assume role with cross-account protection. Permissions grant access to required
    AWS services (Amazon ECR, CloudWatch Logs, AWS X-Ray, Amazon Bedrock, etc.).

    Args:
        role_name: IAM role name to create (must be unique in account).
        account_id: AWS account ID for resource ARNs and trust policy conditions.
        region: AWS region for service-specific resource ARNs.
        additional_ssm_paths: Additional SSM parameter paths beyond default prefix.
        additional_permissions: Additional IAM policy statements for agent-specific
            requirements (e.g., Amazon DynamoDB permissions for Order Agent).

    Returns:
        ARN of created IAM role for use in Amazon Bedrock AgentCore deployment.
    """
    iam = boto3.client("iam")
    policy_name = f"{role_name.replace('-role', '')}-policy"

    # Trust policy allowing Amazon Bedrock AgentCore to assume this role
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AssumeRolePolicy",
                "Effect": "Allow",
                "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
                "Action": "sts:AssumeRole",
                # Condition block prevents cross-account role assumption by restricting
                # to Amazon Bedrock AgentCore runtimes in this account only. Without
                # these conditions, AgentCore in another AWS account could potentially
                # assume this role and access resources.
                "Condition": {
                    "StringEquals": {"aws:SourceAccount": account_id},
                    "ArnLike": {
                        "aws:SourceArn": f"arn:aws:bedrock-agentcore:{region}:{account_id}:*"
                    },
                },
            }
        ],
    }

    # Create or get existing role
    try:
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description=f"Role for {role_name} AgentCore Runtime",
        )
        role_arn = response["Role"]["Arn"]
        logger.info(f"Created role: {role_arn}")
    except iam.exceptions.EntityAlreadyExistsException:
        response = iam.get_role(RoleName=role_name)
        role_arn = response["Role"]["Arn"]
        logger.info(f"Role already exists: {role_arn}")

    # SSM paths to grant access
    ssm_paths = [SSM_PATH_PREFIX]
    if additional_ssm_paths:
        ssm_paths.extend(additional_ssm_paths)

    ssm_resources = [
        f"arn:aws:ssm:{region}:{account_id}:parameter{path}"
        for path in ssm_paths
    ]

    # Base permissions policy for Amazon Bedrock AgentCore runtime
    policy_statements = [
        # === Amazon ECR Container Image Access ===
        # Amazon Bedrock AgentCore pulls agent Docker image from ECR for container deployment
        {
            "Sid": "ECRImageAccess",
            "Effect": "Allow",
            "Action": ["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"],
            "Resource": [f"arn:aws:ecr:{region}:{account_id}:repository/*"],
        },
        {
            "Sid": "ECRTokenAccess",
            "Effect": "Allow",
            "Action": ["ecr:GetAuthorizationToken"],
            "Resource": "*",
        },
        # === Amazon CloudWatch Logs ===
        # Container stdout/stderr automatically streamed to CloudWatch for debugging
        {
            "Effect": "Allow",
            "Action": ["logs:DescribeLogStreams", "logs:CreateLogGroup"],
            "Resource": [
                f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*"
            ],
        },
        {
            "Effect": "Allow",
            "Action": ["logs:DescribeLogGroups"],
            "Resource": [f"arn:aws:logs:{region}:{account_id}:log-group:*"],
        },
        {
            "Effect": "Allow",
            "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
            "Resource": [
                f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*"
            ],
        },
        # === AWS X-Ray Distributed Tracing ===
        # StrandsTelemetry exports OpenTelemetry traces to X-Ray for observability
        {
            "Effect": "Allow",
            "Action": [
                "xray:PutTraceSegments",
                "xray:PutTelemetryRecords",
                "xray:GetSamplingRules",
                "xray:GetSamplingTargets",
            ],
            "Resource": ["*"],
        },
        {
            "Effect": "Allow",
            "Resource": "*",
            "Action": "cloudwatch:PutMetricData",
            "Condition": {
                "StringEquals": {"cloudwatch:namespace": "bedrock-agentcore"}
            },
        },
        # === Amazon Bedrock AgentCore Workload Identity ===
        # Required for agent authentication and workload access token management
        {
            "Sid": "GetAgentAccessToken",
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:GetWorkloadAccessToken",
                "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
                "bedrock-agentcore:GetWorkloadAccessTokenForUserId",
            ],
            "Resource": [
                f"arn:aws:bedrock-agentcore:{region}:{account_id}:workload-identity-directory/default",
                f"arn:aws:bedrock-agentcore:{region}:{account_id}:workload-identity-directory/default/workload-identity/*",
            ],
        },
        # === Amazon Bedrock Model Invocation ===
        # Enables agent to call Amazon Bedrock foundation models (Claude, etc.) for inference
        {
            "Sid": "BedrockModelInvocation",
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
            ],
            "Resource": [
                "arn:aws:bedrock:*::foundation-model/*",
                f"arn:aws:bedrock:{region}:{account_id}:*",
            ],
        },
        # === AWS Systems Manager Parameter Store ===
        # Runtime configuration (agent URLs, table names) read from SSM at startup
        {
            "Sid": "SSMParameterAccess",
            "Effect": "Allow",
            "Action": ["ssm:GetParameter"],
            "Resource": ssm_resources,
        },
        # === Amazon Bedrock AgentCore Runtime Operations ===
        # A2A client tools (a2a_send_message, a2a_discover_agent) invoke AgentCore APIs
        {
            "Sid": "AgentCoreRuntimeAccess",
            "Effect": "Allow",
            "Action": ["bedrock-agentcore:*"],
            "Resource": "*",
        },
    ]

    # Add additional permissions if provided (e.g., DynamoDB for Order Agent)
    if additional_permissions:
        policy_statements.extend(additional_permissions)

    permissions_policy = {
        "Version": "2012-10-17",
        "Statement": policy_statements,
    }

    # Attach policy
    iam.put_role_policy(
        RoleName=role_name,
        PolicyName=policy_name,
        PolicyDocument=json.dumps(permissions_policy),
    )
    logger.info(f"Attached policy: {policy_name}")

    # Wait for IAM propagation
    logger.info("Waiting for IAM propagation...")
    time.sleep(10)

    return role_arn


def delete_agentcore_role(role_name: str) -> bool:
    """Delete IAM execution role and attached inline policies.

    Removes inline policies first, then deletes the IAM role. Safe to call on
    non-existent roles (returns False without error).

    Args:
        role_name: Name of IAM role to delete.

    Returns:
        True if role deleted successfully, False if role not found or error occurred.
    """
    iam = boto3.client("iam")
    policy_name = f"{role_name.replace('-role', '')}-policy"

    try:
        # First delete inline policies
        try:
            iam.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
            logger.info(f"Deleted policy: {policy_name}")
        except iam.exceptions.NoSuchEntityException:
            logger.info(f"Policy {policy_name} not found")

        # Delete the role
        iam.delete_role(RoleName=role_name)
        logger.info(f"Deleted role: {role_name}")
        return True

    except iam.exceptions.NoSuchEntityException:
        logger.info(f"Role {role_name} not found")
        return False
    except Exception as e:
        logger.error(f"Error deleting role: {e}")
        return False
