from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_iam as iam,
    CfnOutput,
    RemovalPolicy,
    Duration,
    CustomResource,
    custom_resources as cr,
    aws_lambda as lambda_
)
from constructs import Construct
import os

class WebAppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, webapp_dir: str, 
                 cognito_user_pool_client_id=None, websocket_api=None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create S3 Bucket
        webapp_bucket = s3.Bucket(
            self, "WebAppS3Bucket",
            bucket_name = Stack.of(self).stack_name.lower() + "-" + Stack.of(self).account + "-webapp",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,  
            auto_delete_objects=True,
            enforce_ssl=True,  # Fix for AwsSolutions-S10
            encryption=s3.BucketEncryption.S3_MANAGED,  # Fix for AwsSolutions-S1
            versioned=True,  # Fix for AwsSolutions-S2
            server_access_logs_prefix="access-logs/"  # Fix for AwsSolutions-S1
        )

        # Create IAM role for the Lambda function with scoped CloudWatch permissions
        config_generator_role = iam.Role(
            self, "ConfigGeneratorLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )
        
        # Add CloudWatch Logs permissions with scoped resources
        config_generator_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            resources=[
                f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/*-ConfigGeneratorLambda*"
            ]
        ))

        # Create Lambda function to generate config.js
        config_generator_lambda = lambda_.Function(
            self, "ConfigGeneratorLambda",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.lambda_handler",
            role=config_generator_role,
            code=lambda_.Code.from_inline("""
import os
import json
import boto3
import cfnresponse

def lambda_handler(event, context):
    response_data = {}
    
    try:
        if event['RequestType'] == 'Create' or event['RequestType'] == 'Update':
            s3 = boto3.client('s3')
            
            # Get parameters from the event
            bucket_name = event['ResourceProperties']['BucketName']
            region = event['ResourceProperties']['Region']
            client_id = event['ResourceProperties']['ClientId']
            ws_endpoint = event['ResourceProperties']['WsEndpoint']
            
            # Generate config.js content
            config_content = f'''// Auto-generated during deployment
window.APP_CONFIG = {{
    AWS_REGION: '{region}',
    CLIENT_ID: '{client_id}',
    WS_ENDPOINT: '{ws_endpoint}'
}};'''
            
            # Upload config.js to S3
            s3.put_object(
                Bucket=bucket_name,
                Key='config.js',
                Body=config_content,
                ContentType='application/javascript'
            )
            
            response_data['Message'] = 'Config file generated successfully'
        
        cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
    except Exception as e:
        print(f"Error: {str(e)}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {"Error": str(e)})
"""),
            timeout=Duration.seconds(30)
        )

        # Grant the Lambda function permissions to write to the S3 bucket
        webapp_bucket.grant_write(config_generator_lambda)

        # Create a custom role for the BucketDeployment Lambda
        deployment_lambda_role = iam.Role(
            self, "BucketDeploymentLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )
        
        # Add CloudWatch Logs permissions with scoped resources
        deployment_lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            resources=[
                f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/*BucketDeployment*"
            ]
        ))
        
        # Add S3 permissions needed for deployment
        deployment_lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "s3:GetObject*",
                "s3:GetBucket*",
                "s3:List*",
                "s3:DeleteObject*",
                "s3:PutObject*",
                "s3:Abort*"
            ],
            resources=[
                webapp_bucket.bucket_arn,
                f"{webapp_bucket.bucket_arn}/*"
            ]
        ))

        # Deploy local files to the bucket
        s3deploy.BucketDeployment(self, "WebAppS3BucketDeployment",
            sources=[s3deploy.Source.asset(webapp_dir)],
            destination_bucket=webapp_bucket,
            role=deployment_lambda_role
        )

        # Create Origin Access Control for CloudFront
        oac = cloudfront.CfnOriginAccessControl(
            self, "CloudFrontOriginAccessControl",
            origin_access_control_config=cloudfront.CfnOriginAccessControl.OriginAccessControlConfigProperty(
                name=f"{Stack.of(self).stack_name}-OAC",
                origin_access_control_origin_type="s3",
                signing_behavior="always",
                signing_protocol="sigv4",
                description="Origin Access Control for WebApp S3 Bucket"
            )
        )

        # Create CloudFront Distribution
        distribution = cloudfront.CloudFrontWebDistribution(
            self, "CloudFrontDistribution",
            origin_configs=[
                cloudfront.SourceConfiguration(
                    s3_origin_source=cloudfront.S3OriginConfig(
                        s3_bucket_source=webapp_bucket,
                        # Do not specify origin_access_identity here
                    ),
                    behaviors=[
                        cloudfront.Behavior(
                            is_default_behavior=True,
                            compress=True,
                            allowed_methods=cloudfront.CloudFrontAllowedMethods.GET_HEAD_OPTIONS,
                            cached_methods=cloudfront.CloudFrontAllowedCachedMethods.GET_HEAD_OPTIONS,
                            default_ttl=Duration.seconds(300),
                            min_ttl=Duration.seconds(0),
                            max_ttl=Duration.seconds(1200),
                            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                        )
                    ]
                )
            ],
            default_root_object="index.html",
            http_version=cloudfront.HttpVersion.HTTP2,
            viewer_certificate=cloudfront.ViewerCertificate.from_cloud_front_default_certificate(),
            price_class=cloudfront.PriceClass.PRICE_CLASS_100
        )
        
        # Apply Origin Access Control to the distribution's S3 origin
        cfn_distribution = distribution.node.default_child
        cfn_distribution.add_property_override(
            "DistributionConfig.Origins.0.OriginAccessControlId", 
            oac.get_att("Id")
        )
        
        # Create bucket policy for OAC
        webapp_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[f"{webapp_bucket.bucket_arn}/*"],
                principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
                conditions={
                    "StringEquals": {
                        "AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{distribution.distribution_id}"
                    }
                }
            )
        )

        # Create a custom resource to generate the config.js file
        config_generator = CustomResource(
            self, "ConfigGenerator",
            service_token=cr.Provider(
                self, "ConfigGeneratorProvider",
                on_event_handler=config_generator_lambda
            ).service_token,
            properties={
                "BucketName": webapp_bucket.bucket_name,
                "Region": self.region,
                "ClientId": cognito_user_pool_client_id,
                "WsEndpoint": f"wss://{websocket_api.ref}.execute-api.{self.region}.amazonaws.com"
            }
        )

        # Make sure the config generator runs after the bucket deployment
        config_generator.node.add_dependency(webapp_bucket)

        # Outputs
        CfnOutput(
            self, "CloudFrontURL",
            value=distribution.distribution_domain_name,
            description="CloudFront Distribution Domain Name"
        )

        CfnOutput(
            self, "BucketName",
            value=webapp_bucket.bucket_name,
            description="S3 Bucket Name"
        )
