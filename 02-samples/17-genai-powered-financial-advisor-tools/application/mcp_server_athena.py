#This sample application is intended solely for educational and knowledge-sharing purposes. It is not designed to provide investment guidance or financial advice.

import os
import re
import time
import json
from typing import List, Dict, Any, Optional
import logging
import sys
import yaml
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from mcp.server.fastmcp import FastMCP

# Initialize logging first
logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s:%(lineno)d | %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("athena_mcp")

# Load configuration from YAML file
def load_config():
    """Load configuration from prereqs_config.yaml"""
    config_path = Path(__file__).parent / "prerequisites" / "prereqs_config.yaml"
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            #logger.info(f"✅ Loaded configuration from {config_path}")
            return config
    except Exception as e:
        logger.warning(f"⚠️  Could not load config from {config_path}: {e}. Using defaults.")
        return {}

config = load_config()

# Extract values from YAML config
AWS_REGION = os.environ.get("AWS_REGION", config.get("region_name", "us-west-2"))
S3_BUCKET_ATHENA = config.get("s3_bucket_name_for_athena", "")
S3_OUTPUT = os.environ.get("S3_OUTPUT", f"s3://{S3_BUCKET_ATHENA}/" if S3_BUCKET_ATHENA else "s3://default-athena-bucket/")
DATABASE = config.get("database_name", "financial_advisor")
ATHENA_WORKGROUP = os.environ.get("ATHENA_WORKGROUP")

POLL_INTERVAL_SECONDS = 1
logger.info(f"📋 Configuration: Database={DATABASE}")

try:
    mcp = FastMCP(
        name="database_tools",
    )
    logger.info("✅ Athena MCP server initialized successfully")
except Exception as e:
    err_msg = f"Error: {str(e)}"
    logger.error(f"{err_msg}")


def boto3_clients(region_name: str = AWS_REGION):
    athena = boto3.client("athena", region_name=region_name)
    glue = boto3.client("glue", region_name=region_name)
    return athena, glue

def start_and_wait_athena_query(
    athena_client,
    query_str: str,
    database: str,
    s3_output: str = S3_OUTPUT,
    workgroup: Optional[str] = ATHENA_WORKGROUP,
    poll_interval: float = POLL_INTERVAL_SECONDS,
) -> Dict[str, Any]:
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
    started = start_and_wait_athena_query(athena_client, sql, database)
    qid = started["QueryExecutionId"]
    state = started["QueryExecution"]["Status"]["State"]
    if state != "SUCCEEDED":
        reason = started["QueryExecution"]["Status"].get("StateChangeReason", "<no reason>")
        raise RuntimeError(f"Athena query {qid} failed: {state} - {reason}")
    rows = fetch_query_results(athena_client, qid)
    return rows

def get_database_tables_via_athena(athena_client, database: str = DATABASE) -> List[str]:
    rows = query_to_table_rows(athena_client, "SHOW TABLES", database=database)
    tables = []
    for row in rows:
        if not row:
            continue
        candidate = row[0].strip()
        if candidate and "table" not in candidate.lower():
            tables.append(candidate)
    return list(dict.fromkeys(tables))

def ensure_select_has_limit(sql: str, limit: int = 500) -> str:
    s = sql.strip().rstrip(";")
    if re.match(r"^\s*select\b", s, flags=re.I):
        if re.search(r"\blimit\s+\d+\b", s, flags=re.I):
            return s
        else:
            return s + f" LIMIT {limit}"
    return s

def execute_sql_and_get_results(athena_client, sql: str, database: str = DATABASE, limit: int = 500) -> Dict[str, Any]:
    try:
        sql_to_run = ensure_select_has_limit(sql, limit=limit)
        started = start_and_wait_athena_query(athena_client, sql_to_run, database)
        qid = started["QueryExecutionId"]
        state = started["QueryExecution"]["Status"]["State"]
        if state != "SUCCEEDED":
            return {"success": False, "error": started["QueryExecution"]["Status"].get("StateChangeReason", "unknown"), "state": state}
        rows = fetch_query_results(athena_client, qid)
        if not rows:
            return {"success": True, "header": [], "rows": [], "query_execution_id": qid}
        header = rows[0]
        data_rows = rows[1:]
        return {"success": True, "header": header, "rows": data_rows, "query_execution_id": qid}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def execute_sql_query(sql_query: str, description: str = "") -> dict:
    """
    Execute a SQL query on the financial advisor database.
    
    The calling agent should generate the SQL based on the schema in its system prompt.
    This tool simply executes the provided SQL and returns results.

    Args:
        sql_query: The SQL query to execute (generated by the agent based on schema in its prompt)
        description: Optional description of what the query does (for logging)

    Returns:
        dict: Query results containing:
            - success: Boolean indicating if query succeeded
            - header: List of column names
            - rows: List of data rows
            - query_execution_id: Athena query execution ID
            - sql_query: The SQL that was executed
            - error: Error message if query failed
    """
    try:
        athena_client, _ = boto3_clients()
        
        logger.info(f"🔍 Executing SQL query: {description if description else sql_query[:100]}...")
        logger.info(f"📝 SQL: {sql_query}")
        
        # Execute query directly (agent already validated SQL generation)
        results = execute_sql_and_get_results(athena_client, sql_query, database=DATABASE, limit=200)
        
        if not results.get("success"):
            error_msg = f"Query execution failed: {results.get('error')}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "sql_query": sql_query
            }
        
        logger.info(f"✅ Query executed successfully, returned {len(results.get('rows', []))} rows")
        
        # Add SQL to results for transparency
        results["sql_query"] = sql_query
        
        return results
        
    except Exception as e:
        error_msg = f"Error in execute_sql_query: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg
        }

@mcp.tool()
def get_tables_list() -> dict:
    """
    Get a simple list of all available tables in the database.
    
    Note: The agent already has the complete schema in its system prompt.
    This tool is only for quick reference if needed.
    
    Returns:
        dict: List of table names
    """
    try:
        athena_client, _ = boto3_clients()
        tables = get_database_tables_via_athena(athena_client, database=DATABASE)
        
        return {
            "success": True,
            "tables": tables,
            "table_count": len(tables),
            "note": "Complete schema with columns is available in your system prompt"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    mcp.run()
