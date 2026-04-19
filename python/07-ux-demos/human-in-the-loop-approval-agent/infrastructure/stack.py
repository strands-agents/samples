# Copyright 2026 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""CDK stack for Order Approval Agent deployed to AgentCore Runtime."""

import os

from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    aws_iam as iam,
    aws_s3 as s3,
    aws_bedrock_agentcore_alpha as agentcore,
)
from cdk_nag import NagSuppressions
from constructs import Construct

class OrderApprovalStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        model_id = "us.amazon.nova-pro-v1:0"
        base_model_id = model_id.split(".", 1)[-1]  # strips the "us." prefix

        # S3 bucket for session state
        session_bucket = s3.Bucket(
            self,
            "SessionBucket",
            bucket_name=f"{self.stack_name.lower()}-sessions-{self.account}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
        )

        NagSuppressions.add_resource_suppressions(
            session_bucket,
            [
                {"id": "AwsSolutions-S1", "reason": "Prototype: access logging not required for this demo workload."},
                {"id": "AwsSolutions-S10", "reason": "Prototype: SSL enforcement not required for this demo workload."},
            ],
            apply_to_children=True,
        )

        # Build agent image from local Dockerfile and push to CDK-managed ECR
        agent_runtime_artifact = agentcore.AgentRuntimeArtifact.from_asset(
            os.path.join(os.path.dirname(__file__), "..", "src")
        )

        # AgentCore Runtime with IAM authorizer
        agent_runtime = agentcore.Runtime(
            self,
            "AgentRuntime",
            runtime_name=f"{self.stack_name.replace('-', '_')}_OrderApproval",
            agent_runtime_artifact=agent_runtime_artifact,
            description="Order approval agent with multi-agent graph and human-in-the-loop interrupt",
            environment_variables={
                "SESSION_BUCKET": session_bucket.bucket_name,
                "AWS_DEFAULT_REGION": self.region,
                "MODEL_ID": model_id,
            },
            authorizer_configuration=agentcore.RuntimeAuthorizerConfiguration.using_iam(),
        )

        # Add custom permissions the auto-created role doesn't cover
        agent_runtime.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=[
                    f"arn:aws:bedrock:{self.region}:{self.account}:inference-profile/{model_id}",
                    f"arn:aws:bedrock:us-east-1::foundation-model/{base_model_id}",
                    f"arn:aws:bedrock:us-east-2::foundation-model/{base_model_id}",
                    f"arn:aws:bedrock:us-west-2::foundation-model/{base_model_id}",
                ],
            )
        )
        agent_runtime.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:ListBucket",
                ],
                resources=[
                    session_bucket.bucket_arn,
                    f"{session_bucket.bucket_arn}/*",
                ],
            )
        )

        NagSuppressions.add_resource_suppressions_by_path(
            self,
            f"/{self.stack_name}/AgentRuntime/ExecutionRole/DefaultPolicy/Resource",
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": (
                        "The agent requires read/write access to all objects within the session bucket "
                        "to store and retrieve session state files. The bucket/* wildcard is intentional "
                        "and scoped to this specific bucket ARN."
                    ),
                }
            ],
        )
        agent_runtime.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock-agentcore:GetWorkloadAccessToken",
                    "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
                    "bedrock-agentcore:GetWorkloadAccessTokenForUserId",
                ],
                resources=[
                    f"arn:aws:bedrock-agentcore:{self.region}:{self.account}:workload-identity-directory/default"
                ],
            )
        )

        # Outputs
        CfnOutput(self, "AgentRuntimeArn", value=agent_runtime.agent_runtime_arn)
        CfnOutput(self, "AgentRuntimeId", value=agent_runtime.agent_runtime_id)
        CfnOutput(self, "SessionBucketName", value=session_bucket.bucket_name)
        CfnOutput(self, "ModelId", value=model_id)
