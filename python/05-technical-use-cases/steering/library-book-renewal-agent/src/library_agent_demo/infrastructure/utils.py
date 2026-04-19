"""Utilities for infrastructure integration and CDK output retrieval."""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class CDKOutputError(Exception):
    """Exception raised when CDK outputs cannot be retrieved."""

    pass


def get_cdk_outputs(stack_name: str) -> dict[str, Any]:
    """Get CDK stack outputs using the AWS CLI.

    Args:
        stack_name: Name of the CDK stack

    Returns:
        Dictionary of stack outputs

    Raises:
        CDKOutputError: If outputs cannot be retrieved
    """
    try:
        # Use AWS CLI to get stack outputs
        result = subprocess.run(
            [
                "aws",
                "cloudformation",
                "describe-stacks",
                "--stack-name",
                stack_name,
                "--query",
                "Stacks[0].Outputs",
                "--output",
                "json",
                "--no-cli-pager",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        outputs_list = json.loads(result.stdout)

        # Convert list of outputs to dictionary
        outputs = {}
        for output in outputs_list:
            key = output.get("OutputKey")
            value = output.get("OutputValue")
            if key and value:
                outputs[key] = value

        logger.info(f"Retrieved {len(outputs)} outputs from stack {stack_name}")
        return outputs

    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to get CDK outputs for stack {stack_name}: {e.stderr}"
        logger.error(error_msg)
        raise CDKOutputError(error_msg) from e
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse CDK outputs JSON: {e}"
        logger.error(error_msg)
        raise CDKOutputError(error_msg) from e


def get_gateway_url_from_cdk(stack_name: str = "LibraryAgentGatewayStack") -> str:
    """Get the AgentCore Gateway URL from CDK outputs.

    Args:
        stack_name: Name of the CDK stack containing the gateway

    Returns:
        The gateway URL

    Raises:
        CDKOutputError: If the gateway URL cannot be retrieved
    """
    try:
        outputs = get_cdk_outputs(stack_name)

        gateway_url = outputs.get("GatewayUrl")
        if not gateway_url:
            raise CDKOutputError(f"GatewayUrl not found in stack {stack_name} outputs")

        logger.info(f"Retrieved gateway URL: {gateway_url}")
        return gateway_url

    except CDKOutputError:
        raise
    except Exception as e:
        error_msg = f"Unexpected error retrieving gateway URL: {e}"
        logger.error(error_msg)
        raise CDKOutputError(error_msg) from e


def get_gateway_no_policy_url_from_cdk(stack_name: str = "LibraryAgentGatewayStackNoPolicy") -> str:
    """Get the AgentCore Gateway URL (no policy) from CDK outputs.

    Args:
        stack_name: Name of the CDK stack containing the gateway without policy

    Returns:
        The gateway URL

    Raises:
        CDKOutputError: If the gateway URL cannot be retrieved
    """
    return get_gateway_url_from_cdk(stack_name)


def get_gateway_id_from_cdk(stack_name: str = "LibraryAgentGatewayStack") -> str:
    """Get the AgentCore Gateway ID from CDK outputs.

    Args:
        stack_name: Name of the CDK stack containing the gateway

    Returns:
        The gateway ID

    Raises:
        CDKOutputError: If the gateway ID cannot be retrieved
    """
    try:
        outputs = get_cdk_outputs(stack_name)

        gateway_id = outputs.get("GatewayId")
        if not gateway_id:
            raise CDKOutputError(f"GatewayId not found in stack {stack_name} outputs")

        logger.info(f"Retrieved gateway ID: {gateway_id}")
        return gateway_id

    except CDKOutputError:
        raise
    except Exception as e:
        error_msg = f"Unexpected error retrieving gateway ID: {e}"
        logger.error(error_msg)
        raise CDKOutputError(error_msg) from e


def check_stack_exists(stack_name: str) -> bool:
    """Check if a CDK stack exists and is deployed.

    Args:
        stack_name: Name of the CDK stack to check

    Returns:
        True if stack exists and is in a valid state, False otherwise
    """
    try:
        result = subprocess.run(
            [
                "aws",
                "cloudformation",
                "describe-stacks",
                "--stack-name",
                stack_name,
                "--query",
                "Stacks[0].StackStatus",
                "--output",
                "text",
                "--no-cli-pager",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        stack_status = result.stdout.strip()
        valid_statuses = [
            "CREATE_COMPLETE",
            "UPDATE_COMPLETE",
            "UPDATE_ROLLBACK_COMPLETE",
        ]

        is_valid = stack_status in valid_statuses
        logger.info(f"Stack {stack_name} status: {stack_status} (valid: {is_valid})")
        return is_valid

    except subprocess.CalledProcessError:
        logger.info(f"Stack {stack_name} does not exist or is not accessible")
        return False


def get_cdk_context() -> dict[str, Any]:
    """Get CDK context from cdk.json file.

    Returns:
        Dictionary of CDK context values

    Raises:
        CDKOutputError: If cdk.json cannot be read
    """
    try:
        cdk_json_path = Path("cdk.json")
        if not cdk_json_path.exists():
            raise CDKOutputError("cdk.json file not found")

        with open(cdk_json_path) as f:
            cdk_config = json.load(f)

        context = cdk_config.get("context", {})
        logger.info(f"Retrieved CDK context with {len(context)} entries")
        return context

    except (OSError, json.JSONDecodeError) as e:
        error_msg = f"Failed to read CDK context: {e}"
        logger.error(error_msg)
        raise CDKOutputError(error_msg) from e
