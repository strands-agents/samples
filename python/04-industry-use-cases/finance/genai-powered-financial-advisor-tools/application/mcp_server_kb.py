#This sample application is intended solely for educational and knowledge-sharing purposes. It is not designed to provide investment guidance or financial advice.
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import logging
import os
import sys
from typing import Any, Dict, List
from pathlib import Path
import yaml

from strands import Agent, tool
from strands_tools import current_time, retrieve

from mcp.server.fastmcp import FastMCP

import boto3

logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s:%(lineno)d | %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("kb_mcp")

# Load configuration from YAML file
def load_config():
    """Load configuration from prereqs_config.yaml"""
    config_path = Path(__file__).parent / "prerequisites" / "prereqs_config.yaml"
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            logger.info(f"✅ Loaded configuration from {config_path}")
            return config
    except Exception as e:
        logger.warning(f"⚠️  Could not load config from {config_path}: {e}. Using defaults.")
        return {}

config = load_config()

# Extract values from YAML config
AWS_REGION = os.environ.get("AWS_REGION", config.get("region_name", "us-west-2"))
logger.info(f"📍 Using AWS region: {AWS_REGION}")

try:
    mcp = FastMCP(
        name="kb_tools",
    )
    logger.info("✅ Knowledge Bases MCP server initialized successfully")
except Exception as e:
    err_msg = f"Error: {str(e)}"
    logger.error(f"{err_msg}")

@mcp.tool()
async def knowledge_base_list(region_name: str = None) -> List[Dict[str, Any]]:
    """Extract the list of Knowledge Bases on Amazon Bedrock

    Args:
        region_name: name of the AWS region (optional, defaults to config or environment variable)

    Returns:
        List of knowledge bases 
    """
    # Use provided region_name, or fall back to AWS_REGION from config/env
    region = region_name if region_name else AWS_REGION
    logger.info(f"🔍 Listing knowledge bases in region: {region}")
    
    bedrock_client = boto3.client("bedrock-agent", region_name=region)

    try:
        response = bedrock_client.list_knowledge_bases()
        knowledge_bases = response.get('knowledgeBaseSummaries', [])
        logger.info(f"✅ Retrieved {len(knowledge_bases)} knowledge bases from {region}")
        return knowledge_bases

    except Exception as e:
        logger.error(f"❌ Error listing knowledge bases in {region}: {e}")
        return []
    
if __name__ == "__main__":
    mcp.run()
