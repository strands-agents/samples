"""Amazon DynamoDB table creation and data seeding utilities.

Provides helper functions for creating DynamoDB tables, seeding sample data,
and cleanup operations used across the multi-agent tutorial notebooks.

Key functions:
- create_orders_table: Create DynamoDB table with ecommerce order schema
- seed_orders: Load sample orders from JSON file into DynamoDB
- delete_orders_table: Clean up DynamoDB table during resource deletion
"""

import json
import logging
from decimal import Decimal
from pathlib import Path
from typing import Any

import boto3

logger = logging.getLogger(__name__)


def create_orders_table(table_name: str, region: str) -> dict[str, Any]:
    """Create Amazon DynamoDB table for storing customer orders.

    Creates a table with order_id as the partition key using on-demand billing.
    Checks if table already exists before attempting creation.

    Args:
        table_name: Name for the DynamoDB table (e.g., "ecommerce-orders").
        region: AWS region for table creation (e.g., "us-west-2").

    Returns:
        Dictionary with table ARN and status information.

    Example:
        >>> result = create_orders_table("ecommerce-orders", "us-west-2")
        >>> print(result["table_arn"])
        arn:aws:dynamodb:us-west-2:123456789012:table/ecommerce-orders
    """
    dynamodb = boto3.resource("dynamodb", region_name=region)
    dynamodb_client = boto3.client("dynamodb", region_name=region)

    # Check if table exists
    existing_tables = dynamodb_client.list_tables()["TableNames"]
    if table_name in existing_tables:
        logger.info(f"Table {table_name} already exists")
        table = dynamodb.Table(table_name)
        return {
            "table_arn": table.table_arn,
            "status": "existing",
            "message": f"Table {table_name} already exists",
        }

    # Create new table
    logger.info(f"Creating table: {table_name}")
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "order_id", "KeyType": "HASH"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "order_id", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    logger.info("Waiting for table creation...")
    table.wait_until_exists()
    logger.info(f"Table created: {table.table_arn}")

    return {
        "table_arn": table.table_arn,
        "status": "created",
        "message": f"Table {table_name} created successfully",
    }


def seed_orders(table_name: str, json_file: Path, region: str) -> dict[str, Any]:
    """Seed DynamoDB table with sample order data from JSON file.

    Loads orders from JSON file and writes them to DynamoDB. Uses Decimal
    type for numeric values to comply with DynamoDB requirements.

    Args:
        table_name: Name of the DynamoDB table to seed.
        json_file: Path to JSON file containing order data.
        region: AWS region for DynamoDB client.

    Returns:
        Dictionary with seeding statistics (count, order IDs).

    Example:
        >>> result = seed_orders(
        ...     "ecommerce-orders",
        ...     Path("sample_data/orders.json"),
        ...     "us-west-2"
        ... )
        >>> print(f"Seeded {result['count']} orders")
        Seeded 6 orders
    """
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)

    # Load and seed sample orders
    # Note: DynamoDB requires Decimal instead of float, so we use parse_float=Decimal
    with open(json_file) as f:
        sample_orders = json.load(f, parse_float=Decimal)

    logger.info(f"Seeding {len(sample_orders)} orders...")
    order_ids = []
    for order in sample_orders:
        table.put_item(Item=order)
        order_id = order["order_id"]
        customer_name = order["customer_name"]
        status = order["status"]
        product_ids = order["product_ids"]
        logger.info(
            f"  {order_id}: {customer_name} - {status} - products {product_ids}"
        )
        order_ids.append(order_id)

    logger.info("Orders seeded successfully!")

    return {
        "count": len(sample_orders),
        "order_ids": order_ids,
        "message": f"Seeded {len(sample_orders)} orders to {table_name}",
    }


def delete_orders_table(table_name: str, region: str) -> dict[str, Any]:
    """Delete DynamoDB table and all its data.

    Args:
        table_name: Name of the DynamoDB table to delete.
        region: AWS region for DynamoDB client.

    Returns:
        Dictionary with deletion status.

    Example:
        >>> result = delete_orders_table("ecommerce-orders", "us-west-2")
        >>> print(result["message"])
        Table ecommerce-orders deleted successfully
    """
    dynamodb_client = boto3.client("dynamodb", region_name=region)

    try:
        logger.info(f"Deleting DynamoDB table: {table_name}")
        dynamodb_client.delete_table(TableName=table_name)
        logger.info("Table deleted successfully")
        return {
            "status": "deleted",
            "message": f"Table {table_name} deleted successfully",
        }
    except Exception as e:
        logger.error(f"Error deleting table: {e}")
        return {
            "status": "error",
            "message": f"Error deleting table {table_name}: {str(e)}",
        }
