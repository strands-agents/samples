# AWS Systems Manager Parameter Store Paths
# Use-case based prefix "/ecommerce-assistant/" enables IAM policies to grant
# access to all parameters for this deployment using single wildcard pattern:
# "arn:aws:ssm:*:*:parameter/ecommerce-assistant/*"

# This scopes permissions to only this multi-agent system without exposing
# unrelated SSM parameters. See utils/iam.py for IAM permission configuration.
SSM_ORDER_AGENT_URL = "/ecommerce-assistant/order-agent-url"
SSM_PRODUCT_AGENT_URL = "/ecommerce-assistant/product-agent-url"
SSM_ORDERS_TABLE = "/ecommerce-assistant/orders-table"

# Amazon DynamoDB table name for order storage
DYNAMODB_TABLE_NAME = "ecommerce-orders"

# Agent names must use underscores only, never hyphens
ORDER_AGENT_NAME = "ecommerce_order_agent"
PRODUCT_AGENT_NAME = "ecommerce_product_agent"
ORCHESTRATOR_AGENT_NAME = "ecommerce_orchestrator"

# Role Names (derived from agent names)
ORDER_ROLE_NAME = f"{ORDER_AGENT_NAME}-role"
PRODUCT_ROLE_NAME = f"{PRODUCT_AGENT_NAME}-role"
ORCHESTRATOR_ROLE_NAME = f"{ORCHESTRATOR_AGENT_NAME}-role"
