from aws_cdk import (
    Stack,
    aws_cognito as cognito,
    aws_lambda as lambda_,
    aws_iam as iam,
    CfnOutput,
    RemovalPolicy,
    Duration,
    CustomResource
)
from constructs import Construct
import os


class CognitoStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Cognito User Pool
        user_pool = cognito.UserPool(self, "UserPool",
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            user_verification=cognito.UserVerificationConfig(
                email_subject="Verify your email for our application",
                email_body="Your verification code is {####}"
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
                temp_password_validity=Duration.days(7)  
            ),
            mfa=cognito.Mfa.OFF,
            sign_in_aliases=cognito.SignInAliases(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
                fullname=cognito.StandardAttribute(required=True, mutable=True)
            ),
            self_sign_up_enabled=True,
            removal_policy=RemovalPolicy.DESTROY
        )

        
        # Create User Pool Client
        user_pool_client = user_pool.add_client("UserPoolClient",
            generate_secret=False,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
                custom=True,
                admin_user_password=True  # If you need admin auth flow
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    implicit_code_grant=False,
                    authorization_code_grant=True
                ),
                scopes=[cognito.OAuthScope.OPENID],
                callback_urls=["http://localhost:3000"]  # Replace with your actual callback URLs
            )
        )

        # Create Identity Pool
        identity_pool = cognito.CfnIdentityPool(self, "IdentityPool",
            allow_unauthenticated_identities=False,
            cognito_identity_providers=[
                cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                    client_id=user_pool_client.user_pool_client_id,
                    provider_name=user_pool.user_pool_provider_name
                )
            ]
        )

        # Create Authenticated Role
        authenticated_role = iam.Role(self, "AuthenticatedRole",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                conditions={
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": identity_pool.ref
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "authenticated"
                    }
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity"
            )
        )

        # Attach Roles to Identity Pool
        cognito.CfnIdentityPoolRoleAttachment(self, "RoleAttachment",
            identity_pool_id=identity_pool.ref,
            roles={
                "authenticated": authenticated_role.role_arn
            }
        )


        # Create Lambda Role
        create_user_function_role = iam.Role(
            self, "CreateUserFunctionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        
        )

        # Grant permissions to Lambda to manage Cognito users
        create_user_function_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    'cognito-idp:AdminCreateUser',
                    'cognito-idp:AdminSetUserPassword'
                ],
                resources=[user_pool.user_pool_arn]
            )
        )

        create_user_function_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=[
                        f"arn:aws:logs:{Stack.of(self).region}:{Stack.of(self).account}:log-group:/aws/lambda/*-CreateDefaultUserFunction*"
                    ]
            )
        )

        # Create Lambda function to create default user
        create_user_function = lambda_.Function(
            self, "CreateDefaultUserFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.lambda_handler",
            code=lambda_.Code.from_asset("code/lambda/BootstrapCognito"),
            timeout=Duration.minutes(1),
            environment={
                'USER_POOL_ID': user_pool.user_pool_id
            },
            role = create_user_function_role
        )
        

        # Create Custom Resource to trigger the Lambda
        custom_resource = CustomResource(
            self, "CreateDefaultUserTrigger",
            service_token=create_user_function.function_arn
        )
        self.user_pool_id = user_pool.user_pool_id
        self.user_pool_client_id = user_pool_client.user_pool_client_id
        # Outputs
        CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=user_pool_client.user_pool_client_id)
        CfnOutput(self, "IdentityPoolId", value=identity_pool.ref)
        CfnOutput(self, "Username", value = custom_resource.get_att("Username").to_string())
        CfnOutput(self, "Password", value = custom_resource.get_att("Password").to_string())
