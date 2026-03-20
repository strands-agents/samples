"""OAuth MCP client for AgentCore Gateway integration."""

import logging
from typing import Any

import boto3
import requests
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient

logger = logging.getLogger(__name__)


def get_oauth_config_from_cloudformation(
    gateway_stack_name: str = "LibraryAgentGatewayStack",
    auth_stack_name: str = "LibraryAgentAuthStack",
    aws_region: str = "us-west-2",
) -> dict[str, str]:
    """Get OAuth configuration from CloudFormation stacks."""
    cf = boto3.client("cloudformation", region_name=aws_region)

    # Get gateway URL
    gateway_response = cf.describe_stacks(StackName=gateway_stack_name)
    gateway_url = None
    for output in gateway_response["Stacks"][0]["Outputs"]:
        if output["OutputKey"] == "GatewayUrl":
            gateway_url = output["OutputValue"]
            break

    # Get auth configuration
    auth_response = cf.describe_stacks(StackName=auth_stack_name)
    user_pool_domain = None
    client_id_arn = None
    client_secret_arn = None

    for output in auth_response["Stacks"][0]["Outputs"]:
        if output["OutputKey"] == "UserPoolDomain":
            user_pool_domain = output["OutputValue"]
        elif output["OutputKey"] == "OAuthClientIdArn":
            client_id_arn = output["OutputValue"]
        elif output["OutputKey"] == "OAuthClientSecretArn":
            client_secret_arn = output["OutputValue"]

    if not all([gateway_url, user_pool_domain, client_id_arn, client_secret_arn]):
        raise ValueError("Missing required CloudFormation outputs")

    # Type assertions since we've verified all values are not None
    assert gateway_url is not None
    assert user_pool_domain is not None
    assert client_id_arn is not None
    assert client_secret_arn is not None

    return {
        "gateway_url": gateway_url,
        "user_pool_domain": user_pool_domain,
        "client_id_arn": client_id_arn,
        "client_secret_arn": client_secret_arn,
        "token_url": f"https://{user_pool_domain}.auth.{aws_region}.amazoncognito.com/oauth2/token",
    }


def get_oauth_credentials_from_secrets(
    client_id_arn: str, client_secret_arn: str, aws_region: str = "us-west-2"
) -> tuple[str, str]:
    """Get OAuth credentials from Secrets Manager."""
    secrets = boto3.client("secretsmanager", region_name=aws_region)

    # Get credentials using full ARNs
    client_id_response = secrets.get_secret_value(SecretId=client_id_arn)
    client_id = client_id_response["SecretString"]

    client_secret_response = secrets.get_secret_value(SecretId=client_secret_arn)
    client_secret = client_secret_response["SecretString"]

    return client_id, client_secret


def fetch_oauth_access_token(client_id: str, client_secret: str, token_url: str) -> str:
    """Fetch OAuth access token."""
    response = requests.post(
        token_url,
        data=f"grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return response.json()["access_token"]


def create_oauth_mcp_client(
    gateway_stack_name: str = "LibraryAgentGatewayStack",
    auth_stack_name: str = "LibraryAgentAuthStack",
    aws_region: str = "us-west-2",
) -> MCPClient:
    """Create MCP client with OAuth authentication from CloudFormation."""
    # Get configuration from CloudFormation
    config = get_oauth_config_from_cloudformation(gateway_stack_name, auth_stack_name, aws_region)

    # Get credentials from Secrets Manager
    client_id, client_secret = get_oauth_credentials_from_secrets(
        config["client_id_arn"], config["client_secret_arn"], aws_region
    )

    # Get access token
    access_token = fetch_oauth_access_token(client_id, client_secret, config["token_url"])

    # Create transport with OAuth token
    def create_transport():
        return streamablehttp_client(config["gateway_url"], headers={"Authorization": f"Bearer {access_token}"})

    return MCPClient(create_transport)


def create_oauth_mcp_client_no_policy(aws_region: str = "us-west-2") -> MCPClient:
    """Create MCP client for the gateway without policy."""
    return create_oauth_mcp_client("LibraryAgentGatewayStackNoPolicy", "LibraryAgentAuthStack", aws_region)


def get_full_tools_list(client: MCPClient) -> list[Any]:
    """List tools with pagination support."""
    try:
        tools = []
        pagination_token = None
        while True:
            tmp_tools = client.list_tools_sync(pagination_token=pagination_token)
            tools.extend(tmp_tools)
            if tmp_tools.pagination_token is None:
                break
            pagination_token = tmp_tools.pagination_token
        return tools
    except Exception as e:
        logger.warning(f"Failed to get gateway tools: {e}")
        return []
