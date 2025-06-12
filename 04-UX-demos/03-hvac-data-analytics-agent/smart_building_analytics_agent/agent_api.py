from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as integrations,
    aws_bedrock as bedrock,
    custom_resources as cr,
    aws_logs as logs,
    Duration,
    CfnOutput,
    RemovalPolicy
)
from constructs import Construct
import os

class AgentApiStack(Stack):
    def __init__(self, scope: Construct, id: str,  
                 cognito_user_pool_id, 
                 cognito_user_pool_client_id, agent_main_function_name: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        agent_lambda_arn = lambda_.Function.from_function_name(self, "AgentFunctionRef", agent_main_function_name).function_arn
        # Create Lambda Layer 
        lambda_layer = lambda_.LayerVersion(
            self, "UtilLambdaLayer",
            layer_version_name="UtilLayer",
            code=lambda_.Code.from_asset("layers/layer-util.zip"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_13]
        )

        # Create Authorizer Function
        authorizer_role = iam.Role(
            self, "AuthorizerFunctionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )
        
        authorizer_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=[
                    f"arn:aws:logs:{Stack.of(self).region}:{Stack.of(self).account}:log-group:/aws/lambda/*-AuthorizerFunction*"
                ]
            )
        )

        authorizer_function = lambda_.Function(
            self, "AuthorizerFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.lambda_handler",
            code=lambda_.Code.from_asset("code/lambda/ApiAuthorizer"),
            environment={
                "USER_POOL_ID": cognito_user_pool_id,
                "CLIENT_ID": cognito_user_pool_client_id
            },
            timeout=Duration.seconds(5),
            memory_size=128,
            layers=[lambda_layer],
            role=authorizer_role
        )

        

        # Create WebSocket API
        websocket_api = apigwv2.CfnApi(
            self, "AgentWSAPI",
            name="AgentWSAPI",
            protocol_type="WEBSOCKET",
            route_selection_expression="$request.body.action"
        )

        authorizer_function.add_permission(
            "WebSocketApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{websocket_api.ref}/*"
        )

        # Create CloudWatch Log Group for API Gateway access logs
        log_group = logs.LogGroup(
            self, "ApiGatewayAccessLogs",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create WebSocket Stage with access logging enabled
        websocket_stage = apigwv2.CfnStage(
            self, "AgentWSAPIStage",
            api_id=websocket_api.ref,
            stage_name="$default",
            auto_deploy=True,
           
        )

        # Create WebSocket Lambda Authorizer
        ws_authorizer = apigwv2.CfnAuthorizer(
            self, "WSLambdaAuthorizer",
            api_id=websocket_api.ref,
            authorizer_type="REQUEST",
            authorizer_uri=f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{authorizer_function.function_arn}/invocations",
            identity_source=["route.request.querystring.jwt"],
            name="WSLambdaAuthorizer"
        )
    

        # Create Lambda Role
        chat_api_role = iam.Role(
            self, "ChatAPIFunctionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        
        )
        
        
        chat_api_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["lambda:InvokeFunction"],
                resources=[agent_lambda_arn]
            )
        )
      


        chat_api_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=[
                    f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/*-ChatAPIFunction*"
                ]
            )
        )
        

        # Create Lambda Function
        chat_api_function = lambda_.Function(
            self, "ChatAPIFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            memory_size=128,
            timeout=Duration.seconds(5),
            handler="index.lambda_handler",
            role=chat_api_role,
            code=lambda_.Code.from_asset("code/lambda/ChatApi"),
            environment={
                "AGENT_LAMBDA_ARN": agent_lambda_arn
            }
        )
        chat_api_function.add_permission(
            "WebSocketApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{websocket_api.ref}/*"
        )

        # Add Lambda Permission for API Gateway
        chat_api_function.add_permission(
            "ChatAPIFunctionResourcePolicy",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{websocket_api.ref}/*"
        )

        # Create Chat Integration
        chat_integration = apigwv2.CfnIntegration(
            self, "ChatIntegration",
            api_id=websocket_api.ref,
            integration_type="AWS_PROXY",
            integration_uri=f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{chat_api_function.function_arn}/invocations"
        )

        # Create WebSocket Routes
        apigwv2.CfnRoute(
            self, "ChatConnectRoute",
            api_id=websocket_api.ref,
            route_key="$connect",
            authorization_type="CUSTOM",
            authorizer_id=ws_authorizer.ref,
            target=f"integrations/{chat_integration.ref}"
        )

        apigwv2.CfnRoute(
            self, "ChatDefaultRoute",
            api_id=websocket_api.ref,
            route_key="$default",
            authorization_type="NONE",
            target=f"integrations/{chat_integration.ref}"
        )

        apigwv2.CfnRoute(
            self, "ChatDisconnectRoute",
            api_id=websocket_api.ref,
            route_key="$disconnect",
            authorization_type="NONE",
            target=f"integrations/{chat_integration.ref}"
        )

        self.websocket_api = websocket_api

        

        