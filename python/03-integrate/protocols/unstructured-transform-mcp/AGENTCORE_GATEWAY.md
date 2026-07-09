# Federating Transform MCP through Amazon Bedrock AgentCore Gateway

This guide covers an alternative deployment pattern for the sample in this folder: instead of an agent connecting directly to `https://mcp.transform.unstructured.io`, you federate Transform MCP as a **target** behind an [Amazon Bedrock AgentCore Gateway](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-target-MCPservers.html), and point the agent at the Gateway's unified MCP endpoint instead.

## What AgentCore Gateway is

AgentCore Gateway is a managed service that turns existing APIs, Lambda functions, and other MCP servers into a single MCP endpoint for your agents. It handles:

- **Inbound auth** to the Gateway itself (who is allowed to call the Gateway's MCP endpoint).
- **Outbound auth** to each federated target (how the Gateway authenticates to Transform MCP, a Lambda function, an OpenAPI backend, etc.), via **credential providers** it manages on your behalf.
- **Tool discovery and indexing**: the Gateway calls each target's `tools/list` and indexes the results into one searchable, unified tool catalog.

## Why federate Transform MCP through a Gateway

For a single-agent sample like the one in this folder, connecting directly to Transform MCP is simplest. Federating through AgentCore Gateway is worth the extra setup when:

- You want **one managed endpoint** in front of several MCP servers (Transform MCP plus internal tools, other vendor MCP servers, etc.), instead of wiring every agent to every server individually.
- You want **credential management centralized** in AWS rather than distributing an `UNSTRUCTURED_API_KEY` (or OAuth client) to every agent runtime.
- You want a **unified tool catalog** with search/discovery across many federated targets, rather than agents each calling `list_tools_sync()` against a fixed set of servers.

## Adding Transform MCP as a Gateway target

Use `bedrock-agentcore-control`'s `create_gateway_target` API with an `mcp` target configuration pointing at Transform MCP's endpoint, and an `OAUTH` credential provider for outbound auth:

```python
import boto3

client = boto3.client("bedrock-agentcore-control", region_name="us-west-2")

response = client.create_gateway_target(
    gatewayIdentifier="<your-gateway-id>",
    name="unstructured-transform",
    description="Unstructured Transform document-processing MCP server",
    targetConfiguration={
        "mcp": {
            "mcpServer": {
                "endpoint": "https://mcp.transform.unstructured.io",
            }
        }
    },
    credentialProviderConfigurations=[
        {
            "credentialProviderType": "OAUTH",
            "credentialProvider": {
                "oauthCredentialProvider": {
                    "providerArn": "<your-oauth-credential-provider-arn>",
                    "scopes": [],
                }
            },
        }
    ],
)
```

Transform MCP's browser OAuth/OIDC flow is a 3-legged, authorization-code grant. After `create_gateway_target` returns, the target sits in `CREATE_PENDING_AUTH` until an admin completes the authorization URL for that credential provider (a one-time, human-in-the-loop step). Once authorized, the Gateway can call the target's `tools/list` and indexes Transform's tools (`transform_files`, `check_transform_status`, `get_transform_results`, `request_file_upload_url`) into the Gateway's unified catalog.

See the AWS docs for the full target configuration schema and current field names:

- [Gateway targets for MCP servers](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-target-MCPservers.html)
- [Gateway target API configuration reference](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-add-target-api-target-config.html)

## Pointing the Strands agent at the Gateway instead

Once the target is authorized and active, update the agent from this sample to connect to the Gateway's MCP endpoint rather than Transform MCP directly. The client code is the same shape (`streamablehttp_client` + `MCPClient`); only the URL and the auth header change, since the Gateway now mediates its own inbound auth:

```python
import os
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient
from strands import Agent

mcp_client = MCPClient(lambda: streamablehttp_client(
    url="<your-agentcore-gateway-mcp-endpoint>",
    headers={"Authorization": f"Bearer {os.environ['GATEWAY_ACCESS_TOKEN']}"},
))

with mcp_client:
    tools = mcp_client.list_tools_sync()
    agent = Agent(model="us.anthropic.claude-sonnet-4-5-20250929-v1:0", tools=tools)
    response = agent("Parse and chunk this document: <public PDF URL>")
```

`tools` returned here may include Transform's tools alongside tools from any other targets federated on the same Gateway. The agent code itself doesn't need to know which target a given tool came from.
