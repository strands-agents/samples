"""
CDK stack for AgentCore Gateway infrastructure.

This stack creates:
- Lambda function for the renewal request MCP server
- AgentCore Gateway with IAM authentication
- Gateway target configuration for the Lambda function
- Necessary IAM roles and permissions
"""

from typing import Any

from aws_cdk import (
    CfnOutput,
    Duration,
    Fn,
    RemovalPolicy,
    Stack,
)
from aws_cdk import (
    aws_bedrockagentcore as bedrockagentcore,
)
from aws_cdk import (
    aws_iam as iam,
)
from aws_cdk import (
    aws_lambda as lambda_,
)
from aws_cdk import (
    aws_logs as logs,
)
from constructs import Construct


class LibraryAgentGatewayStack(Stack):
    """CDK stack for the Library Agent Control Demo AgentCore Gateway."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        stack_name_suffix: str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create IAM role for the Lambda function
        lambda_role = iam.Role(
            self,
            "RenewalServerLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),  # type: ignore
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
        )

        # Create CloudWatch log group for the Lambda function
        log_group = logs.LogGroup(
            self,
            "RenewalServerLogGroup",
            log_group_name=f"/aws/lambda/library-renewal-server{stack_name_suffix}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Create Lambda function for the renewal request MCP server
        renewal_server_function = lambda_.Function(
            self,
            "RenewalServerFunction",
            function_name=f"library-renewal-server{stack_name_suffix}",
            role=lambda_role,  # type: ignore
            log_group=log_group,
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_asset("src/library_agent_demo/infrastructure/lambda"),
            memory_size=1024,
            timeout=Duration.seconds(30),
            environment={
                "LOG_LEVEL": "INFO",
            },
        )

        # Create IAM role for the AgentCore Gateway
        gateway_role = iam.Role(
            self,
            "GatewayRole",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),  # type: ignore
            inline_policies={
                "LambdaInvokePolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["lambda:InvokeFunction"],
                            resources=[renewal_server_function.function_arn],
                        )
                    ]
                ),
                "PolicyEvaluationPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "bedrock-agentcore:PartiallyAuthorizeActions",
                                "bedrock-agentcore:AuthorizeAction",
                                "bedrock-agentcore:GetPolicyEngine",
                                "bedrock-agentcore:GetGateway",
                            ],
                            resources=["*"],
                        )
                    ]
                ),
            },
        )

        # Load tools configuration for the gateway
        tools_config = self._get_tools_configuration()

        # Create CloudWatch log group for gateway logs
        gateway_log_group = logs.LogGroup(
            self,
            "GatewayLogGroup",
            log_group_name=f"/aws/vendedlogs/bedrock-agentcore/gateway/APPLICATION_LOGS/library-agent-gateway{stack_name_suffix}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Create AgentCore Gateway with OAuth authentication
        gateway_name = f"LibraryAgent-Gateway{stack_name_suffix}"
        if len(gateway_name) > 48:
            gateway_name = gateway_name[:48].rstrip("-")

        # Use the base stack suffix for imports (without the additional suffix)
        base_suffix = (
            stack_name_suffix.replace("-no-policy", "") if "-no-policy" in stack_name_suffix else stack_name_suffix
        )

        gateway = bedrockagentcore.CfnGateway(
            self,
            "LibraryAgentGateway",
            name=gateway_name,
            role_arn=gateway_role.role_arn,
            protocol_type="MCP",
            authorizer_type="CUSTOM_JWT",
            authorizer_configuration={
                "customJwtAuthorizer": {
                    "allowedClients": [
                        Fn.import_value(f"LibraryAuth-InteractiveClientId{base_suffix}"),
                        Fn.import_value(f"LibraryAuth-AutomatedClientId{base_suffix}"),
                    ],
                    "discoveryUrl": Fn.sub(
                        "${IssuerDomain}/.well-known/openid-configuration",
                        {
                            "IssuerDomain": Fn.import_value(f"LibraryAuth-IssuerDomain{base_suffix}"),
                        },
                    ),
                }
            },
            exception_level="DEBUG",
        )

        # Create Gateway Target for the renewal server
        bedrockagentcore.CfnGatewayTarget(
            self,
            "RenewalServerTarget",
            gateway_identifier=gateway.attr_gateway_identifier,
            name="renewal-server-target",
            target_configuration=bedrockagentcore.CfnGatewayTarget.TargetConfigurationProperty(
                mcp=bedrockagentcore.CfnGatewayTarget.McpTargetConfigurationProperty(
                    lambda_=bedrockagentcore.CfnGatewayTarget.McpLambdaTargetConfigurationProperty(
                        lambda_arn=renewal_server_function.function_arn,
                        tool_schema=bedrockagentcore.CfnGatewayTarget.ToolSchemaProperty(inline_payload=tools_config),
                    )
                )
            ),
            credential_provider_configurations=[
                bedrockagentcore.CfnGatewayTarget.CredentialProviderConfigurationProperty(
                    credential_provider_type="GATEWAY_IAM_ROLE"
                )
            ],
        )

        # Grant the gateway permission to invoke the Lambda function
        renewal_server_function.grant_invoke(gateway_role)

        # Create delivery source for gateway logs (after gateway is created)
        gateway_delivery_source = logs.CfnDeliverySource(
            self,
            "GatewayDeliverySource",
            name=f"library-gateway-logs-source{stack_name_suffix}",
            log_type="APPLICATION_LOGS",
            resource_arn=gateway.attr_gateway_arn,
        )
        gateway_delivery_source.add_dependency(gateway)

        # Create delivery source for gateway traces
        gateway_traces_delivery_source = logs.CfnDeliverySource(
            self,
            "GatewayTracesDeliverySource",
            name=f"library-gateway-traces-source{stack_name_suffix}",
            log_type="TRACES",
            resource_arn=gateway.attr_gateway_arn,
        )
        gateway_traces_delivery_source.add_dependency(gateway)

        # Create delivery destination for CloudWatch Logs
        gateway_delivery_destination = logs.CfnDeliveryDestination(
            self,
            "GatewayDeliveryDestination",
            name=f"library-gateway-logs-destination{stack_name_suffix}",
            delivery_destination_type="CWL",
            destination_resource_arn=gateway_log_group.log_group_arn,
        )

        # Create delivery destination for X-Ray traces
        gateway_traces_delivery_destination = logs.CfnDeliveryDestination(
            self,
            "GatewayTracesDeliveryDestination",
            name=f"library-gateway-traces-destination{stack_name_suffix}",
            delivery_destination_type="XRAY",
        )

        # Create delivery to connect source and destination for logs
        gateway_log_delivery = logs.CfnDelivery(
            self,
            "GatewayLogDelivery",
            delivery_source_name=gateway_delivery_source.name,
            delivery_destination_arn=gateway_delivery_destination.attr_arn,
        )
        gateway_log_delivery.add_dependency(gateway_delivery_source)
        gateway_log_delivery.add_dependency(gateway_delivery_destination)

        # Create delivery to connect source and destination for traces
        gateway_traces_delivery = logs.CfnDelivery(
            self,
            "GatewayTracesDelivery",
            delivery_source_name=gateway_traces_delivery_source.name,
            delivery_destination_arn=gateway_traces_delivery_destination.attr_arn,
        )
        gateway_traces_delivery.add_dependency(gateway_traces_delivery_source)
        gateway_traces_delivery.add_dependency(gateway_traces_delivery_destination)

        # Output important values
        CfnOutput(
            self,
            "RenewalServerFunctionArn",
            value=renewal_server_function.function_arn,
            description="ARN of the renewal server Lambda function",
        )

        CfnOutput(
            self,
            "GatewayId",
            value=gateway.attr_gateway_identifier,
            description="AgentCore Gateway identifier",
        )

        CfnOutput(
            self,
            "GatewayUrl",
            value=gateway.attr_gateway_url,
            description="AgentCore Gateway URL for MCP connections",
        )

        CfnOutput(
            self,
            "GatewayLogGroupArn",
            value=gateway_log_group.log_group_arn,
            description="ARN of the gateway CloudWatch log group",
        )

        # Store outputs as instance variables for access by other components
        self.gateway_url = gateway.attr_gateway_url
        self.gateway_id = gateway.attr_gateway_identifier
        self.renewal_function_arn = renewal_server_function.function_arn
        self.gateway_log_group_arn = gateway_log_group.log_group_arn

    def _get_tools_configuration(
        self,
    ) -> list[bedrockagentcore.CfnGatewayTarget.ToolDefinitionProperty]:
        """Get the tools configuration for the gateway target."""
        return [
            bedrockagentcore.CfnGatewayTarget.ToolDefinitionProperty(
                name="renew_book",
                description="Renew a library book for a specified period",
                input_schema=bedrockagentcore.CfnGatewayTarget.SchemaDefinitionProperty(
                    type="object",
                    description="Input schema for book renewal",
                    properties={
                        "book": bedrockagentcore.CfnGatewayTarget.SchemaDefinitionProperty(  # noqa: E501
                            type="string", description="The book identifier to renew"
                        ),
                        "renewal_period": bedrockagentcore.CfnGatewayTarget.SchemaDefinitionProperty(  # noqa: E501
                            type="integer",
                            description="Number of days to renew the book for",
                        ),
                        "library_card_number": bedrockagentcore.CfnGatewayTarget.SchemaDefinitionProperty(  # noqa: E501
                            type="string", description="The user's library card number"
                        ),
                    },
                    required=["book", "renewal_period", "library_card_number"],
                ),
            )
        ]
