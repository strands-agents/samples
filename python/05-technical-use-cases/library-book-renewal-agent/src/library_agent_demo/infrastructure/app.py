#!/usr/bin/env python3
"""
CDK application for the Library Agent Control Demo.

This app creates the AgentCore Gateway infrastructure needed for the
renewal request MCP server.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from aws_cdk import App, Environment  # noqa: E402

from library_agent_demo.infrastructure.auth_stack import (  # noqa: E402
    LibraryAgentAuthStack,
)
from library_agent_demo.infrastructure.gateway_stack import (  # noqa: E402
    LibraryAgentGatewayStack,
)


def main() -> None:
    """Main CDK application entry point."""
    app = App()

    # Get environment configuration
    account = os.environ.get("CDK_DEFAULT_ACCOUNT")
    region = os.environ.get("CDK_DEFAULT_REGION", "us-west-2")

    if not account:
        raise ValueError("CDK_DEFAULT_ACCOUNT environment variable must be set")

    env = Environment(account=account, region=region)

    # Create stack name suffix for multiple deployments
    stack_suffix = os.environ.get("STACK_SUFFIX", "")
    if stack_suffix and not stack_suffix.startswith("-"):
        stack_suffix = f"-{stack_suffix}"

    # Create the auth stack first (gateway depends on it)
    auth_stack = LibraryAgentAuthStack(
        app,
        "LibraryAgentAuthStack",
        stack_name_suffix=stack_suffix,
        stack_name=f"LibraryAgentAuthStack{stack_suffix}",
        env=env,
        description="OAuth authentication infrastructure for Library Agent Control Demo",
    )

    # Create the first gateway stack (with policy)
    gateway_stack = LibraryAgentGatewayStack(
        app,
        "LibraryAgentGatewayStack",
        stack_name_suffix=stack_suffix,
        stack_name=f"LibraryAgentGatewayStack{stack_suffix}",
        env=env,
        description="AgentCore Gateway infrastructure for Library Agent Control Demo",
    )

    # Create the second gateway stack (without policy)
    gateway_stack_no_policy = LibraryAgentGatewayStack(
        app,
        "LibraryAgentGatewayStackNoPolicy",
        stack_name_suffix=f"{stack_suffix}-no-policy",
        stack_name=f"LibraryAgentGatewayStackNoPolicy{stack_suffix}",
        env=env,
        description="AgentCore Gateway infrastructure without policy for Library Agent Control Demo",
    )

    # Both gateway stacks depend on auth stack
    gateway_stack.add_dependency(auth_stack)
    gateway_stack_no_policy.add_dependency(auth_stack)

    app.synth()


if __name__ == "__main__":
    main()
