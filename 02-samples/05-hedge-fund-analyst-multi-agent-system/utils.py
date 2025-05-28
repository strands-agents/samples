# This file contain utility functions that are used across the mutli agent
# solution
import re
import os
import json
import yaml
import time
import boto3
import zipfile
import logging
from io import BytesIO
from pathlib import Path
from typing import Union, Dict, Optional

# set a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PYTHON_TIMEOUT: int = 180
PYTHON_RUNTIME: str = "python3.12"

# Initialize S3 client
s3_client = boto3.client('s3')
# Initialize the bedrock runtime client. This is used to 
# query search results from the FMC and Meraki KBs
bedrock_agent_runtime_client = boto3.client('bedrock-agent-runtime') 

def load_config(config_file: Union[Path, str]) -> Optional[Dict]:
    """
    Load configuration from a local file.

    :param config_file: Path to the local file
    :return: Dictionary with the loaded configuration
    """
    try:
        config_data: Optional[Dict] = None
        logger.info(f"Loading config from local file system: {config_file}")
        content = Path(config_file).read_text()
        config_data = yaml.safe_load(content)
        logger.info(f"Loaded config from local file system: {config_data}")
    except Exception as e:
        logger.error(f"Error loading config from local file system: {e}")
        config_data = None
    return config_data
