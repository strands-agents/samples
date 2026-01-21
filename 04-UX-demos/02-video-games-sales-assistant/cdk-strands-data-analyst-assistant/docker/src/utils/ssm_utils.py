"""
AWS Systems Manager Parameter Store Utilities

This module provides functions to interact with AWS Systems Manager Parameter Store
for retrieving configuration parameters. Parameters are stored with the prefix
'/agentcore-data-analyst-assistant/' followed by the parameter name.

Parameters:
- SECRET_ARN: ARN of the AWS Secrets Manager secret containing database credentials
- AURORA_RESOURCE_ARN: ARN of the Aurora Serverless cluster
- DATABASE_NAME: Name of the database to connect to
- DATABASE_USERNAME: Username for database connection
- RAW_QUERY_RESULTS_TABLE_NAME: DynamoDB table for storing raw query results
- CONVERSATION_TABLE_NAME: DynamoDB table for storing conversation data
- MAX_RESPONSE_SIZE_BYTES: Maximum size of query responses in bytes (default: 25600)
- LAST_NUMBER_OF_MESSAGES: Number of last messages to retrieve (default: 20)
"""

import boto3
import os
from botocore.exceptions import ClientError

# Project ID for SSM parameter path prefix
PROJECT_ID = os.environ.get('PROJECT_ID', 'N/A')

def get_ssm_client():
    """
    Creates and returns an SSM client using default AWS configuration.

    Returns:
        boto3.client: SSM client
    """
    return boto3.client("ssm")


def get_ssm_parameter(param_name):
    """
    Retrieves a parameter from AWS Systems Manager Parameter Store.

    Args:
        param_name: Name of the parameter without the project prefix

    Returns:
        str: The parameter value

    Raises:
        ClientError: If there's an error retrieving the parameter
    """
    client = get_ssm_client()
    full_param_name = f"/{PROJECT_ID}/{param_name}"

    try:
        response = client.get_parameter(Name=full_param_name, WithDecryption=True)
        return response["Parameter"]["Value"]
    except ClientError as e:
        print("\n" + "=" * 70)
        print("❌ SSM PARAMETER RETRIEVAL ERROR")
        print("=" * 70)
        print(f"📋 Parameter: {full_param_name}")
        print(f"💥 Error: {e}")
        print("=" * 70 + "\n")
        raise


def load_config():
    """
    Loads all required configuration parameters from SSM.

    Returns:
        dict: Configuration dictionary with all parameters

    Note:
        Required parameters will raise ValueError if not found.
        Optional parameters will be set to None or default values if not found.
    """
    # Define the parameters to load
    param_keys = [
        "SECRET_ARN",
        "AURORA_RESOURCE_ARN",
        "DATABASE_NAME",
        "DATABASE_USERNAME",
        "RAW_QUERY_RESULTS_TABLE_NAME",
        "CONVERSATION_TABLE_NAME",
        "MAX_RESPONSE_SIZE_BYTES",
        "LAST_NUMBER_OF_MESSAGES",
    ]

    config = {}

    # Load each parameter
    for key in param_keys:
        try:
            value = get_ssm_parameter(key)
            # Convert to int for specific parameters
            if key in ["MAX_RESPONSE_SIZE_BYTES", "LAST_NUMBER_OF_MESSAGES"]:
                config[key] = int(value)
            else:
                config[key] = value
        except ClientError:
            # Set default values for optional parameters
            if key == "MAX_RESPONSE_SIZE_BYTES":
                config[key] = 25600
            elif key == "LAST_NUMBER_OF_MESSAGES":
                config[key] = 20
            # For required parameters, raise an exception
            elif key in [
                "SECRET_ARN",
                "AURORA_RESOURCE_ARN",
                "DATABASE_NAME",
                "DATABASE_USERNAME",
            ]:
                raise ValueError(
                    f"Required SSM parameter /{PROJECT_ID}/{key} not found"
                )
            # For table names, set to None if not found
            elif key in ["RAW_QUERY_RESULTS_TABLE_NAME", "CONVERSATION_TABLE_NAME"]:
                config[key] = None

    return config