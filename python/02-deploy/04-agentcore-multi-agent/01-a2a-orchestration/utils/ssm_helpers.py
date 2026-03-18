"""AWS Systems Manager Parameter Store helper functions.

Provides utilities for storing and retrieving configuration parameters
used across the multi-agent tutorial notebooks.

Key functions:
- store_ssm_parameter: Store values in SSM Parameter Store
- get_ssm_parameter: Retrieve values from SSM Parameter Store
- delete_parameters: Clean up SSM parameters during resource deletion
"""

import logging
from typing import Any

import boto3

logger = logging.getLogger(__name__)


def store_ssm_parameter(param_name: str, value: str, region: str) -> dict[str, Any]:
    """Store a value in AWS Systems Manager Parameter Store.

    Uses SecureString type for encryption at rest. Overwrites existing
    parameter if present.

    Args:
        param_name: SSM parameter name (e.g., "/ecommerce-assistant/order-agent-url").
        value: Value to store (e.g., agent URL, table name).
        region: AWS region for SSM client.

    Returns:
        Dictionary with parameter name, version, and status message.

    Example:
        >>> result = store_ssm_parameter(
        ...     "/ecommerce-assistant/order-agent-url",
        ...     "https://bedrock-agentcore.us-west-2.amazonaws.com/...",
        ...     "us-west-2"
        ... )
        >>> print(result["message"])
        Stored parameter /ecommerce-assistant/order-agent-url
    """
    ssm = boto3.client("ssm", region_name=region)

    try:
        response = ssm.put_parameter(
            Name=param_name,
            Value=value,
            Type="SecureString",  # Encrypts at rest using default KMS key
            Overwrite=True,  # Update existing parameter, increment version
        )
        logger.info(f"Stored parameter: {param_name}")
        return {
            "parameter_name": param_name,
            "version": response["Version"],
            "message": f"Stored parameter {param_name}",
        }
    except Exception as e:
        logger.error(f"Error storing parameter {param_name}: {e}")
        raise


def get_ssm_parameter(param_name: str, region: str) -> str:
    """Retrieve a value from AWS Systems Manager Parameter Store.

    Args:
        param_name: SSM parameter name to retrieve.
        region: AWS region for SSM client.

    Returns:
        Parameter value string.

    Raises:
        Exception: If parameter cannot be retrieved from SSM.

    Example:
        >>> url = get_ssm_parameter("/ecommerce-assistant/order-agent-url", "us-west-2")
        >>> print(url)
        https://bedrock-agentcore.us-west-2.amazonaws.com/...
    """
    ssm = boto3.client("ssm", region_name=region)

    try:
        # WithDecryption=True required for SecureString plaintext
        response = ssm.get_parameter(Name=param_name, WithDecryption=True)
        url = response["Parameter"]["Value"]
        logger.info(f"Retrieved parameter: {param_name}")
        return url
    except Exception as e:
        logger.error(f"Error retrieving parameter {param_name}: {e}")
        raise


def delete_parameters(param_names: list[str], region: str) -> dict[str, Any]:
    """Delete multiple SSM parameters.

    Args:
        param_names: List of SSM parameter names to delete.
        region: AWS region for SSM client.

    Returns:
        Dictionary with deletion results for each parameter.

    Example:
        >>> result = delete_parameters([
        ...     "/ecommerce-assistant/order-agent-url",
        ...     "/ecommerce-assistant/product-agent-url",
        ... ], "us-west-2")
        >>> print(result["deleted_count"])
        2
    """
    ssm = boto3.client("ssm", region_name=region)

    results = {"deleted": [], "errors": []}

    # Delete individually for granular error handling
    logger.info(f"Deleting {len(param_names)} SSM parameters...")
    for param in param_names:
        try:
            ssm.delete_parameter(Name=param)
            logger.info(f"  Deleted: {param}")
            results["deleted"].append(param)
        except Exception as e:
            logger.error(f"  Error deleting {param}: {e}")
            results["errors"].append({"param": param, "error": str(e)})

    return {
        "deleted_count": len(results["deleted"]),
        "error_count": len(results["errors"]),
        "deleted": results["deleted"],
        "errors": results["errors"],
        "message": f"Deleted {len(results['deleted'])} parameters",
    }
