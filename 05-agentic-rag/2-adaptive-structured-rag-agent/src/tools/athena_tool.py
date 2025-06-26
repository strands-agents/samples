"""
Athena Query Tool for executing SQL queries.
"""
from strands import tool
import boto3
import time
import logging
import os
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

@tool
def run_athena_query(query: str) -> Dict[str, Any]:
    """
    Execute a SQL query on Amazon Athena.
    
    Uses boto3 to execute the query on Athena and returns the results.
    
    Args:
        query: SQL query string to execute
    
    Returns:
        Dict containing either query results or error information
    """
    try:    
        # Create Athena client using the environment variables
        # AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN
        # are automatically used by boto3
        from config import get_config
        config = get_config()
        
        athena_client = boto3.client('athena', region_name=config['aws_region'])
        
        # Start query execution
        logger.info(f"Executing Athena query: {query}")
        response = athena_client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={
                'Database': config['athena_database']
            },
            ResultConfiguration={
                'OutputLocation': config['athena_output_location']
            }
        )
        
        query_execution_id = response['QueryExecutionId']
        logger.info(f"Query execution ID: {query_execution_id}")
        
        # Wait for query to complete
        max_retries = 20  # Avoid infinite loops
        retries = 0

        while retries < max_retries:
            response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
            state = response['QueryExecution']['Status']['State']
            if state == 'SUCCEEDED':
                print("Query succeeded!")
                break
            elif state in ['FAILED', 'CANCELLED']:
                print(f"Query {state.lower()}.")
                break
            else:
                print(f"Query state: {state}, sleeping for 10 seconds")
                time.sleep(2)
                retries += 1
        
        # Check final state
        if state == 'SUCCEEDED':
            # Get query results
            results = athena_client.get_query_results(QueryExecutionId=query_execution_id)
            
            # Process results
            columns = [col['Label'] for col in results['ResultSet']['ResultSetMetadata']['ColumnInfo']]
            rows = results['ResultSet']['Rows'][1:]  # Skip header row
            
            data = []
            for row in rows:
                item = {}
                for i, value in enumerate(row['Data']):
                    # Handle null values
                    if 'VarCharValue' in value:
                        item[columns[i]] = value['VarCharValue']
                    else:
                        item[columns[i]] = None
                data.append(item)
            
            return {
                "success": True,
                "data": data,
                "query": query
            }
        else:
            # Query failed
            error_message = response['QueryExecution']['Status'].get('StateChangeReason', 'Query failed with an Unknown error')
            error_details = response['QueryExecution']['Status'].get('AthenaError', "Query failed with an Unknown Athena error")
            logger.error(f"Query failed response: {response['QueryExecution']['Status']}")
            
            return {
                "success": False,
                "error": error_message,
                "athena_error_details": error_details,
                "query": query
            }
    
    except Exception as e:
        logger.exception("Error executing Athena query")
        return {
            "success": False,
            "error": str(e),
            "query": query
        }
