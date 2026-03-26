"""
CDK stack for OAuth authentication infrastructure.

This stack creates:
- Cognito User Pool for OAuth authentication
- OAuth clients for interactive and automated flows
- Resource server with scopes for the library agent
"""

from typing import Any

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    SecretValue,
    Stack,
)
from aws_cdk import (
    aws_cognito as cognito,
)
from aws_cdk import (
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct


class LibraryAgentAuthStack(Stack):
    """CDK stack for OAuth authentication infrastructure."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        stack_name_suffix: str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Cognito User Pool
        user_pool = cognito.UserPool(
            self,
            "LibraryAgentUserPool",
            user_pool_name=f"library-agent{stack_name_suffix}",
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(
                email=True,
                username=True,
            ),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=12,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
            ),
            account_recovery=cognito.AccountRecovery.NONE,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Create a user in the user pool
        cognito.CfnUserPoolUser(
            self,
            "LibraryAgentUser",
            user_pool_id=user_pool.user_pool_id,
            username="library-user",
            user_attributes=[
                cognito.CfnUserPoolUser.AttributeTypeProperty(
                    name="email",
                    value="library-user@example.com",
                ),
                cognito.CfnUserPoolUser.AttributeTypeProperty(
                    name="email_verified",
                    value="true",
                ),
            ],
            message_action="SUPPRESS",
        )

        # Create user credentials secret
        user_credentials_secret = secretsmanager.Secret(
            self,
            "LibraryUserPassword",
            secret_name=f"library-agent-user-creds{stack_name_suffix}",
            description="Credentials for library agent user",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username": "library-user"}',
                generate_string_key="password",
                exclude_characters='"@/\\',
                include_space=False,
                password_length=16,
                require_each_included_type=True,
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Create User Pool Domain
        user_pool_domain = user_pool.add_domain(
            "LibraryAgentUserPoolDomain",
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=f"library-agent-{self.account}{stack_name_suffix}",
            ),
        )

        # Create resource server scope for library agent
        library_scope = cognito.ResourceServerScope(
            scope_name="library-agent",
            scope_description="Scope for library agent MCP server",
        )

        resource_server = cognito.UserPoolResourceServer(
            self,
            "LibraryResourceServer",
            identifier="library-resource-server",
            user_pool=user_pool,
            scopes=[library_scope],
        )

        oauth_scope = cognito.OAuthScope.resource_server(resource_server, library_scope)

        # OAuth client for interactive flows
        interactive_client = user_pool.add_client(
            "InteractiveClient",
            generate_secret=False,
            prevent_user_existence_errors=True,
            enable_token_revocation=True,
            access_token_validity=Duration.minutes(60),
            refresh_token_validity=Duration.days(60),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                ),
                scopes=[oauth_scope],
                callback_urls=[
                    "http://localhost:9876/callback",  # Local testing
                    "http://localhost:6274/oauth/callback",  # MCP inspector
                    "http://localhost:8090/callback",  # Local example
                ],
            ),
            auth_flows=cognito.AuthFlow(
                user_password=True,
            ),
        )

        # OAuth client for automated flows
        automated_client = user_pool.add_client(
            "AutomatedClient",
            generate_secret=True,
            prevent_user_existence_errors=True,
            enable_token_revocation=True,
            access_token_validity=Duration.minutes(60),
            refresh_token_validity=Duration.days(60),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    client_credentials=True,
                ),
                scopes=[oauth_scope],
            ),
        )

        # Store client ID as a separate secret for easier access
        automated_client_id_secret = secretsmanager.Secret(
            self,
            "AutomatedClientIdSecret",
            secret_name=f"library-agent-oauth-client-id{stack_name_suffix}",
            description="Client ID for automated library agent client",
            secret_string_value=SecretValue.unsafe_plain_text(automated_client.user_pool_client_id),
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Store client secret
        automated_client_secret = secretsmanager.Secret(
            self,
            "AutomatedClientSecret",
            secret_name=f"library-agent-oauth-client-secret{stack_name_suffix}",
            description="Client secret for automated library agent client",
            secret_string_value=automated_client.user_pool_client_secret,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Outputs
        CfnOutput(
            self,
            "UserPoolId",
            value=user_pool.user_pool_id,
            description="Cognito User Pool ID",
            export_name=f"LibraryAuth-UserPoolId{stack_name_suffix}",
        )

        CfnOutput(
            self,
            "IssuerDomain",
            value=user_pool.user_pool_provider_url,
            description="Cognito User Pool Issuer URL",
            export_name=f"LibraryAuth-IssuerDomain{stack_name_suffix}",
        )

        CfnOutput(
            self,
            "UserPoolDomain",
            value=user_pool_domain.domain_name,
            description="Cognito User Pool Domain",
            export_name=f"LibraryAuth-UserPoolDomain{stack_name_suffix}",
        )

        CfnOutput(
            self,
            "InteractiveOAuthClientId",
            value=interactive_client.user_pool_client_id,
            description="Client ID for interactive OAuth flow",
            export_name=f"LibraryAuth-InteractiveClientId{stack_name_suffix}",
        )

        CfnOutput(
            self,
            "AutomatedOAuthClientId",
            value=automated_client.user_pool_client_id,
            description="Client ID for automated OAuth flow",
            export_name=f"LibraryAuth-AutomatedClientId{stack_name_suffix}",
        )

        CfnOutput(
            self,
            "OAuthClientIdArn",
            value=automated_client_id_secret.secret_arn,
            description="ARN of the secret containing the OAuth client ID",
            export_name=f"LibraryAuth-ClientIdArn{stack_name_suffix}",
        )

        CfnOutput(
            self,
            "OAuthClientSecretArn",
            value=automated_client_secret.secret_arn,
            description="ARN of the secret containing the OAuth client secret",
            export_name=f"LibraryAuth-ClientSecretArn{stack_name_suffix}",
        )

        CfnOutput(
            self,
            "UserCredentialsSecretArn",
            value=user_credentials_secret.secret_arn,
            description="ARN of the secret containing the login credentials",
            export_name=f"LibraryAuth-UserCredentialsArn{stack_name_suffix}",
        )
