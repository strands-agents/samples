
import os
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_apigatewayv2 as apigatewayv2,
    aws_s3 as s3,
    Duration,
    Aws
)
from constructs import Construct

PROJECT_PATH = ""

class ToolApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, cognito_user_pool_id: str, 
                 cognito_user_pool_client_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

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
                resources=[f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/*-ToolApiAuthorizerFunction*"]
            )
        )

        authorizer_function = lambda_.Function(
            self, "ToolApiAuthorizerFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.lambda_handler",
            code=lambda_.Code.from_asset("code/lambda/SmartBuildingToolAuthorizer"),
            environment={
                "USER_POOL_ID": cognito_user_pool_id,
                "CLIENT_ID": cognito_user_pool_client_id
            },
            timeout=Duration.seconds(5),
            memory_size=128,
            layers=[lambda_layer],
            role=authorizer_role
        )


        

        # Create entities Lambda role
        entities_role = iam.Role(
            self, "ToolEntitiesAPIFunctionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )
        
        entities_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            resources=[f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/*-ToolEntitiesAPIFunction*"]
        ))

        # Create timeseries Lambda role
        timeseries_role = iam.Role(
            self, "ToolTimeseriesAPIFunctionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )
        
        timeseries_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            resources=[f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/*-ToolTimeseriesAPIFunction*"]
        ))

        # Create Lambda functions
        entities_function = lambda_.Function(
            self, "ToolEntitiesAPIFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.lambda_handler",
            role=entities_role,
            code=lambda_.Code.from_asset("code/lambda/SmartBuildingToolEntitiesApi")
        )

        timeseries_function = lambda_.Function(
            self, "ToolTimeseriesAPIFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.lambda_handler",
            role=timeseries_role,
            code=lambda_.Code.from_asset("code/lambda/SmartBuildingToolTimeseriesApi")
        )

        # Create HTTP API
        http_api = apigatewayv2.CfnApi(
            self, "SBAgentToolAPI",
            name="SBAgentToolAPI",
            protocol_type="HTTP",
            cors_configuration=apigatewayv2.CfnApi.CorsProperty(
                allow_origins=["*"],
                allow_methods=["GET", "POST", "DELETE", "OPTIONS", "PUT"],
                allow_headers=["*"]
            )
        )
        http_api_authorizer = apigatewayv2.CfnAuthorizer(
            self, "ToolApiAuthorizer",
            api_id=http_api.ref,
            authorizer_type="REQUEST",
            authorizer_uri=f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{authorizer_function.function_arn}/invocations",
            identity_source=["$request.header.id_token"],
            authorizer_payload_format_version="2.0",
            name="ToolApiAuthorizer"
        )


        # Create Lambda Integrations
        entities_integration = apigatewayv2.CfnIntegration(
            self, "EntitiesIntegration",
            api_id=http_api.ref,
            integration_type="AWS_PROXY",
            integration_uri=f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{entities_function.function_arn}/invocations",
            payload_format_version="2.0",
            integration_method="POST"  # Lambda integrations always use POST
        )

        timeseries_integration = apigatewayv2.CfnIntegration(
            self, "TimeseriesIntegration",
            api_id=http_api.ref,
            integration_type="AWS_PROXY",
            integration_uri=f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{timeseries_function.function_arn}/invocations",
            payload_format_version="2.0",
            integration_method="POST"
        )

        # Create Routes
        entities_route = apigatewayv2.CfnRoute(
            self, "EntitiesRoute",
            api_id=http_api.ref,
            route_key="GET /entities",  
            target=f"integrations/{entities_integration.ref}",
            authorization_type="CUSTOM",
            authorizer_id=http_api_authorizer.ref
        )

        timeseries_route = apigatewayv2.CfnRoute(
            self, "TimeseriesRoute",
            api_id=http_api.ref,
            route_key="GET /timeseries",  
            target=f"integrations/{timeseries_integration.ref}",
            authorization_type="CUSTOM",
            authorizer_id=http_api_authorizer.ref
        )


        

        # Create API Stage
        api_stage = apigatewayv2.CfnStage(
            self, "SBAgentToolAPIStage",
            api_id=http_api.ref,
            auto_deploy=True,
            stage_name="$default"
        )

        # Add Lambda permissions for API Gateway
        entities_function.add_permission(
            "ToolEntitiesAPIPermission",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=f"arn:aws:execute-api:{Aws.REGION}:{Aws.ACCOUNT_ID}:{http_api.ref}/*/*/entities"
        )

        timeseries_function.add_permission(
            "ToolTimeseriesAPIPermission",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=f"arn:aws:execute-api:{Aws.REGION}:{Aws.ACCOUNT_ID}:{http_api.ref}/*/*/timeseries"
        )

        authorizer_function.add_permission(
            "ToolAuthorizerEntitiesPermission",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=f"arn:aws:execute-api:{Aws.REGION}:{Aws.ACCOUNT_ID}:{http_api.ref}/*"
        )


        # Store references that might be needed by other stacks
        self.api_endpoint = http_api.attr_api_endpoint

        # Outputs
        CfnOutput(self, "api_endpoint", value=http_api.attr_api_endpoint)
