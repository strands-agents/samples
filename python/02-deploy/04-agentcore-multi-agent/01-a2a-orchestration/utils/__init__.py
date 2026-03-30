"""Utility modules for e-commerce multi-agent deployment to Amazon Bedrock AgentCore.

Provides configuration constants, IAM role management, and streaming display utilities
for Order Agent, Product Agent, and Orchestrator Agent deployment and operation.

Modules:
- config: SSM paths, agent names, and deployment configuration constants
- iam: IAM execution role creation and deletion for Amazon Bedrock AgentCore
- streaming: Terminal display utilities for agent streaming event visualization
"""

from .config import (
    SSM_ORDER_AGENT_URL,
    SSM_PRODUCT_AGENT_URL,
    SSM_ORDERS_TABLE,
    DYNAMODB_TABLE_NAME,
    ORDER_AGENT_NAME,
    PRODUCT_AGENT_NAME,
    ORCHESTRATOR_AGENT_NAME,
    ORDER_ROLE_NAME,
    PRODUCT_ROLE_NAME,
    ORCHESTRATOR_ROLE_NAME,
)
from .iam import create_agentcore_role, delete_agentcore_role

__all__ = [
    "SSM_ORDER_AGENT_URL",
    "SSM_PRODUCT_AGENT_URL",
    "SSM_ORDERS_TABLE",
    "DYNAMODB_TABLE_NAME",
    "ORDER_AGENT_NAME",
    "PRODUCT_AGENT_NAME",
    "ORCHESTRATOR_AGENT_NAME",
    "ORDER_ROLE_NAME",
    "PRODUCT_ROLE_NAME",
    "ORCHESTRATOR_ROLE_NAME",
    "create_agentcore_role",
    "delete_agentcore_role",
]
