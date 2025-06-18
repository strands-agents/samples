"""
Configuration management for the NL2SQL agent.
"""
import os
import logging
from typing import Dict, Any


def setup_logging(level=logging.INFO):
    """
    Configure logging for the application.
    
    Args:
        level: Logging level (default: INFO)
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def get_config() -> Dict[str, Any]:
    """
    Get configuration from environment variables.
    
    Returns:
        Dict containing configuration values
    """
    config = {
        # AWS Configuration
        "aws_region": os.environ.get("AWS_REGION", "us-east-1"),  # Default to us-east-1
        
        # Athena Configuration
        "athena_database": os.environ.get("ATHENA_DATABASE", "wealthmanagement-db"),
        "athena_output_location": os.environ.get("ATHENA_OUTPUT_LOCATION", "s3://strands-athena-output-503561448057/"),
        
        # Knowledge Base Configuration
        "knowledge_base_id": os.environ.get("KNOWLEDGE_BASE_ID", "2GKUK2LAUT"),
        
        # Bedrock Configuration
        "bedrock_model_id": os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-sonnet-20240620-v1:0"), 
    }
    
    return config
