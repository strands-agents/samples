"""
This sample application is intended solely for educational and knowledge-sharing purposes. It is not designed to provide investment guidance or financial advice.
Database Schema Retrieval Module

This module provides functions to retrieve database schema from AWS Athena.
Used by chat.py to load schema at application startup.
"""

import os
import time
import yaml
import logging
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path

import boto3

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s:%(lineno)d | %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("athena_schema")

# Load configuration
def load_config():
    """Load configuration from prereqs_config.yaml"""
    config_path = Path(__file__).parent / "prerequisites" / "prereqs_config.yaml"
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"⚠️ Could not load config: {e}")
        return {}

config = load_config()

# Validate required configuration
def validate_config(config: dict) -> None:
    """Validate that required configuration values are present"""
    s3_bucket = (config.get("s3_bucket_name_for_athena") or "").strip()
    database = (config.get("database_name") or "").strip()
    
    missing_configs = []
    if not s3_bucket:
        missing_configs.append("s3_bucket_name_for_athena")
    if not database:
        missing_configs.append("database_name")
    
    if missing_configs:
        error_msg = (
            f"\n{'='*80}\n"
            f"❌ ERROR: Missing required configuration values in prereqs_config.yaml:\n"
            f"   - {', '.join(missing_configs)}\n\n"
            f"📋 Action Required:\n"
            f"   Please setup and configure the database by running:\n"
            f"   application/prerequisites/prereqs_config.yaml\n"
            f"{'='*80}\n"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

# Validate configuration before proceeding
validate_config(config)

# Configuration constants
AWS_REGION = os.environ.get("AWS_REGION", config.get("region_name", "us-west-2"))
S3_BUCKET_ATHENA = config.get("s3_bucket_name_for_athena", "")
S3_OUTPUT = os.environ.get("S3_OUTPUT", f"s3://{S3_BUCKET_ATHENA}/")
DATABASE = config.get("database_name", "")
ATHENA_WORKGROUP = os.environ.get("ATHENA_WORKGROUP")
POLL_INTERVAL_SECONDS = 1

# Module-level schema cache
fa_db_schema = None


def boto3_clients(region_name: str = AWS_REGION):
    """Create and return Athena client (Glue not needed for schema retrieval)"""
    athena = boto3.client("athena", region_name=region_name)
    return athena, None  # Return tuple for backward compatibility

def start_and_wait_athena_query(
    athena_client,
    query_str: str,
    database: str,
    s3_output: str = S3_OUTPUT,
    workgroup: Optional[str] = ATHENA_WORKGROUP,
    poll_interval: float = POLL_INTERVAL_SECONDS,
) -> Dict[str, Any]:
    """Execute an Athena query and wait for completion"""
    params = {
        "QueryString": query_str,
        "QueryExecutionContext": {"Database": database},
        "ResultConfiguration": {"OutputLocation": s3_output},
    }
    if workgroup:
        params["WorkGroup"] = workgroup

    resp = athena_client.start_query_execution(**params)
    query_execution_id = resp["QueryExecutionId"]

    while True:
        qe = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
        state = qe["QueryExecution"]["Status"]["State"]
        if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
            return {"QueryExecutionId": query_execution_id, "QueryExecution": qe["QueryExecution"]}
        time.sleep(poll_interval)


def fetch_query_results(athena_client, query_execution_id: str, max_pages: int = 100) -> List[List[str]]:
    """Fetch results from a completed Athena query"""
    rows_out = []
    next_token = None
    pages = 0
    while True:
        args = {"QueryExecutionId": query_execution_id}
        if next_token:
            args["NextToken"] = next_token
        resp = athena_client.get_query_results(**args)
        for r in resp.get("ResultSet", {}).get("Rows", []):
            data = [col.get("VarCharValue", "") for col in r.get("Data", [])]
            rows_out.append(data)
        next_token = resp.get("NextToken")
        pages += 1
        if not next_token or pages >= max_pages:
            break
    return rows_out


def query_to_table_rows(athena_client, sql: str, database: str = DATABASE) -> List[List[str]]:
    """Execute a query and return results as rows"""
    started = start_and_wait_athena_query(athena_client, sql, database)
    qid = started["QueryExecutionId"]
    state = started["QueryExecution"]["Status"]["State"]
    if state != "SUCCEEDED":
        reason = started["QueryExecution"]["Status"].get("StateChangeReason", "<no reason>")
        raise RuntimeError(f"Athena query {qid} failed: {state} - {reason}")
    rows = fetch_query_results(athena_client, qid)
    return rows


def get_database_tables_via_athena(athena_client, database: str = DATABASE) -> List[str]:
    """Get list of tables in the database"""
    rows = query_to_table_rows(athena_client, "SHOW TABLES", database=database)
    tables = []
    for row in rows:
        if not row:
            continue
        candidate = row[0].strip()
        if candidate and "table" not in candidate.lower():
            tables.append(candidate)
    return list(dict.fromkeys(tables))


def describe_table_via_athena(athena_client, table_name: str, database: str = DATABASE) -> List[Dict[str, str]]:
    """Get column information for a specific table"""
    rows = query_to_table_rows(athena_client, f"DESCRIBE {table_name}", database=database)
    result = []
    for row in rows:
        if not row:
            continue
        if any(h.lower() in ("col_name", "name", "column") for h in row):
            continue
        col_name = row[0].strip() if len(row) > 0 else ""
        col_type = row[1].strip() if len(row) > 1 else ""
        col_comment = row[2].strip() if len(row) > 2 else ""
        if col_name:
            result.append({"name": col_name, "type": col_type, "comment": col_comment})
    return result


def get_database_schema_via_athena(athena_client, database: str = DATABASE) -> Dict[str, Any]:
    """
    Get complete schema for all tables in the database.
    
    Args:
        athena_client: Boto3 Athena client
        database: Database name
        
    Returns:
        Dictionary mapping table names to column information
    """
    global fa_db_schema
    
    # Validate database parameter
    if not database or not database.strip():
        error_msg = (
            "\n❌ ERROR: Database name is empty or not configured.\n"
            "📋 Please setup and configure the database by running:\n"
            "   python application/prerequisites/retrieve_schema.py\n"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    schema = {}
    tables = get_database_tables_via_athena(athena_client, database=database)
    logger.info(f"📊 Found {len(tables)} tables in database '{database}'")
    
    for table in tables:
        try:
            columns = describe_table_via_athena(athena_client, table, database=database)
            schema[table] = columns
            logger.info(f"  ✓ {table}: {len(columns)} columns")
        except Exception as e:
            schema[table] = {"error": str(e)}
            logger.error(f"  ✗ {table}: {str(e)}")
    
    # Update module-level cache
    fa_db_schema = schema
    
    return schema
