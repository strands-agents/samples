"""
AWS Systems Manager Parameter Store Utilities

This module provides functions to interact with AWS Systems Manager Parameter Store
for retrieving configuration parameters. Parameters are stored with the prefix
'/strands-data-analyst-assistant/' followed by the parameter name.

Required SSM Parameters:
- SECRET_ARN: ARN of the AWS Secrets Manager secret containing database credentials
- AURORA_RESOURCE_ARN: ARN of the Aurora Serverless cluster
- DATABASE_NAME: Name of the database to connect to

Optional SSM Parameters:
- QUESTION_ANSWERS_TABLE: DynamoDB table for storing query results
- AGENT_INTERACTIONS_TABLE_NAME: DynamoDB table for storing agent interactions
- MAX_RESPONSE_SIZE_BYTES: Maximum size of query responses in bytes (default: 25600)
"""

import boto3
import os
from botocore.exceptions import ClientError

# Default AWS region
DEFAULT_REGION = "us-east-1"

# Project ID for SSM parameter path prefix - get from environment variable
PROJECT_ID = os.environ.get('PROJECT_ID', 'strands-data-analyst-assistant')


def get_ssm_client(region_name=None):
    """
    Creates and returns an SSM client.
    
    Args:
        region_name: AWS region where the SSM parameters are stored
        
    Returns:
        boto3.client: SSM client
    """
    if not region_name:
        region_name = os.environ.get("AWS_REGION", DEFAULT_REGION)
        
    session = boto3.session.Session()
    return session.client(service_name="ssm", region_name=region_name)


def get_ssm_parameter(param_name, region_name=None):
    """
    Retrieves a parameter from AWS Systems Manager Parameter Store.
    
    Args:
        param_name: Name of the parameter without the project prefix
        region_name: AWS region where the parameter is stored
        
    Returns:
        str: The parameter value
        
    Raises:
        ClientError: If there's an error retrieving the parameter
    """
    client = get_ssm_client(region_name)
    full_param_name = f"/{PROJECT_ID}/{param_name}"
    
    try:
        response = client.get_parameter(
            Name=full_param_name,
            WithDecryption=True
        )
        return response['Parameter']['Value']
    except ClientError as e:
        print("\n" + "="*70)
        print("❌ SSM PARAMETER RETRIEVAL ERROR")
        print("="*70)
        print(f"📋 Parameter: {full_param_name}")
        print(f"💥 Error: {e}")
        print("="*70 + "\n")
        raise


def load_config(region_name=None):
    """
    Loads all required configuration parameters from SSM.
    
    Args:
        region_name: AWS region where the parameters are stored
        
    Returns:
        dict: Configuration dictionary with all parameters
        
    Note:
        Required parameters will raise ValueError if not found.
        Optional parameters will be set to None or default values if not found.
    """
    # Define the parameters to load (matching CDK stack parameter names)
    param_keys = [
        "SECRET_ARN",
        "CLUSTER_ARN", 
        "DATABASE_NAME",
        "DATABASE_USERNAME",
        "RAW_QUERY_RESULTS_TABLE_NAME",
        "CONVERSATION_TABLE_NAME",
        "MAX_RESPONSE_SIZE_BYTES",
        "LAST_NUMBER_OF_MESSAGES"
    ]
    
    config = {}
    
    # Get AWS region from environment or use default
    if not region_name:
        region_name = os.environ.get("AWS_REGION", DEFAULT_REGION)
    
    config["AWS_REGION"] = region_name
    
    # Load each parameter
    for key in param_keys:
        try:
            config[key] = get_ssm_parameter(key, region_name)
        except ClientError:
            # Set default values for optional parameters
            if key == "MAX_RESPONSE_SIZE_BYTES":
                config[key] = "25600"
            elif key == "LAST_NUMBER_OF_MESSAGES":
                config[key] = "20"
            # For required parameters, raise an exception
            elif key in ["SECRET_ARN", "CLUSTER_ARN", "DATABASE_NAME", "DATABASE_USERNAME"]:
                raise ValueError(f"Required SSM parameter /{PROJECT_ID}/{key} not found")
            # For table names, set to None if not found
            elif key in ["RAW_QUERY_RESULTS_TABLE_NAME", "CONVERSATION_TABLE_NAME"]:
                config[key] = None
    
    # Convert numeric parameters to int if they exist
    if "MAX_RESPONSE_SIZE_BYTES" in config:
        try:
            config["MAX_RESPONSE_SIZE_BYTES"] = int(config["MAX_RESPONSE_SIZE_BYTES"])
        except ValueError:
            config["MAX_RESPONSE_SIZE_BYTES"] = 25600
    
    if "LAST_NUMBER_OF_MESSAGES" in config:
        try:
            config["LAST_NUMBER_OF_MESSAGES"] = int(config["LAST_NUMBER_OF_MESSAGES"])
        except ValueError:
            config["LAST_NUMBER_OF_MESSAGES"] = 20
    
    return config