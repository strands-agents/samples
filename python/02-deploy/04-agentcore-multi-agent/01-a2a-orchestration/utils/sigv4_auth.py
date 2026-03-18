"""AWS Signature Version 4 authentication for httpx clients.

Provides SigV4 request signing for httpx HTTP clients to authenticate requests
to Amazon Bedrock AgentCore API endpoints. Implements proper connection header
removal and credential refresh handling required for AgentCore inter-agent calls.

Key features:
- Connection header removal to prevent SignatureDoesNotMatch errors
- Single auth_flow method with httpx sync/async dispatching
- Fresh signer creation per request for IAM role credential refresh
- Integration with A2AClientToolProvider via httpx_client_args parameter

Based on AWS sample:
awslabs/amazon-bedrock-agentcore-samples/.../streamable_http_sigv4.py
"""

from typing import Generator

import httpx
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials


class SigV4HTTPXAuth(httpx.Auth):
    """Sign httpx requests with AWS Signature Version 4 for Amazon Bedrock AgentCore.

    Enables A2AClientToolProvider to authenticate with Amazon Bedrock AgentCore-hosted
    agents by signing HTTP requests according to AWS SigV4 protocol. Handles connection
    header removal and credential refresh required for AgentCore API calls.
    """

    def __init__(self, credentials: Credentials, service: str, region: str):
        """Initialize AWS SigV4 authentication.

        Args:
            credentials: AWS credentials from boto3.Session().get_credentials().
            service: AWS service name for signing scope (use "bedrock-agentcore").
            region: AWS region for signing scope (e.g., "us-west-2").
        """
        self.credentials = credentials
        self.service = service
        self.region = region
        # Fresh signer created per request to handle IAM role credential refresh

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        """Sign HTTP request with AWS SigV4 before transmission.

        Connection header must be removed before signing. Amazon Bedrock AgentCore
        server excludes it from signature calculation, causing SignatureDoesNotMatch
        errors if included in client signature.

        From AWS sample: "Header 'connection' = 'keep-alive' is not used in
        calculating the request signature on the server-side"

        Args:
            request: Outbound httpx request to sign.

        Yields:
            Signed request with AWS SigV4 authorization headers added.
        """
        headers = dict(request.headers)

        # Remove connection header to prevent SignatureDoesNotMatch error
        headers.pop("connection", None)  # Remove if present, ignore if absent

        aws_request = AWSRequest(
            method=request.method,
            url=str(request.url),
            data=request.content,
            headers=headers,
        )

        # Get frozen credentials to ensure latest values from IAM role auto-refresh.
        # Critical for long-running processes with temporary security credentials.
        frozen_credentials = self.credentials.get_frozen_credentials()

        # Create fresh signer with current credentials
        signer = SigV4Auth(frozen_credentials, self.service, self.region)

        # Sign request with AWS SigV4 protocol
        signer.add_auth(aws_request)

        # Add signature headers to original request
        request.headers.update(dict(aws_request.headers))

        yield request
