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
            auto_delete_objects=True
        )

        # Create Lambda function to generate config.js
        config_generator_lambda = lambda_.Function(
            self, "ConfigGeneratorLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
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

        # Deploy local files to the bucket
        s3deploy.BucketDeployment(self, "WebAppS3BucketDeployment",
            sources=[s3deploy.Source.asset(webapp_dir)],
            destination_bucket=webapp_bucket
        )

        # Create CloudFront OAI
        origin_access_identity = cloudfront.OriginAccessIdentity(
            self, "CloudFrontOriginAccessIdentity",
            comment="OAI for WebAppS3Bucket"
        )

        # Grant read permissions to CloudFront
        webapp_bucket.grant_read(origin_access_identity)

        # Create CloudFront Distribution
        distribution = cloudfront.Distribution(
            self, "CloudFrontDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    bucket=webapp_bucket,
                    origin_access_identity=origin_access_identity
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy(
                    self, "CachePolicy",
                    default_ttl=Duration.seconds(300),
                    min_ttl=Duration.seconds(0),
                    max_ttl=Duration.seconds(1200),
                )
            ),
            enabled=True,
            default_root_object="index.html",
            http_version=cloudfront.HttpVersion.HTTP2
        )

        # Create bucket policy
        webapp_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[f"{webapp_bucket.bucket_arn}/*"],
                principals=[iam.CanonicalUserPrincipal(
                    origin_access_identity.cloud_front_origin_access_identity_s3_canonical_user_id
                )]
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
