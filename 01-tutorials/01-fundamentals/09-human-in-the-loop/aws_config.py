"""
AWS configuration for the HR assistant agent.
This file contains the AWS configuration for the Bedrock model.
"""

import os
import boto3
from botocore.config import Config

# AWS configuration
AWS_REGION = "us-east-1"  # Replace with your AWS region
AWS_PROFILE = "bhrsrini-admin"   # Replace with your AWS profile name

def get_bedrock_session():
    """Get a Bedrock client with the configured AWS credentials.
    
    Returns:
        A Bedrock client.
    """
    # Configure AWS session
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    
    return session
