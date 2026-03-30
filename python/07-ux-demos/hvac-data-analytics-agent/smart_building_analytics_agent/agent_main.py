from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_s3 as s3,
    CfnOutput,
    Duration,
    CustomResource,
    RemovalPolicy
)
from constructs import Construct
import os 



class AgentStack(Stack):
    def __init__(self, scope: Construct, id: str, websocket_api, agent_main_function_name, tool_api_endpoint,  **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create S3 bucket for the agent
        agent_bucket = s3.Bucket(
            self, "AgentDataBucket",
            removal_policy=RemovalPolicy.RETAIN,  # RETAIN to keep the bucket when stack is deleted
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True
        )

        lambda_layer = lambda_.LayerVersion(
            self, "STLambdaLayer",
            layer_version_name="STLayer",
            code=lambda_.Code.from_asset("layers/layer-strands.zip"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_12]
        )

        # Create IAM Role for Lambda
        lambda_role = iam.Role(
            self, "AgentMainFunctionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
               
            ]
        )

       
       
        lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
            resources=[
                f"arn:aws:bedrock:{self.region}:{self.account}:inference-profile/*",
                "arn:aws:bedrock:*::foundation-model/*"
            ]
        ))

        lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "execute-api:Invoke",
                "execute-api:ManageConnections"
            ],
            resources=[f"arn:aws:execute-api:{Stack.of(self).region}:{Stack.of(self).account}:{websocket_api.ref}/$default/POST/@connections/*"]
        ))

        # Add S3 permissions to Lambda role
        lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket",
                "s3:DeleteObject"
            ],
            resources=[
                agent_bucket.bucket_arn,
                f"{agent_bucket.bucket_arn}/threads/*"
            ]
        ))

        lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            resources=[f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/" + agent_main_function_name + "*"]
        ))

        # Create Lambda Function
        agent_function = lambda_.Function(
            self, "AgentMainFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            function_name=agent_main_function_name,
            handler="index.lambda_handler",
            code=lambda_.Code.from_asset("code/lambda/STAgentMain"),
            memory_size=512,
            timeout=Duration.seconds(180),
            environment={
                "WS_API_ENDPOINT": websocket_api.attr_api_endpoint,
                "AGENT_BUCKET": agent_bucket.bucket_name,
                "TOOL_API_ENDPOINT": tool_api_endpoint,
                "LANGFUSE_HOST": "",
                "LANGFUSE_PK": "",
                "LANGFUSE_SK": ""
                
            },
            role=lambda_role,
            layers=[lambda_layer]
        )

        # Output the S3 bucket name
        CfnOutput(
            self, "AgentDataBucketName",
            value=agent_bucket.bucket_name,
            description="S3 bucket for agent data storage"
        )




