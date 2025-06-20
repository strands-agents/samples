"""
NL2SQL Agent implementation using Strands SDK.
"""
import os
import logging
from strands import Agent

from src.tools.knowledge_base_tool import get_schema
from src.tools.athena_tool import run_athena_query
from src.tools.sqllite_tool import run_sqlite_query

logger = logging.getLogger(__name__)

def create_nl2sql_agent(environment: str = "local") -> Agent:
    """
    Create and configure the NL2SQL agent with appropriate tools and system prompt.
    
    Returns:
        Agent: Configured Strands agent instance
    """
    # Define the system prompt for the NL2SQL agent
    system_prompt = """
    You are an NL2SQL agent that converts natural language questions into SQL queries.
    
    Your task is to:
    1. Understand the user's question
    2. Generate a valid SQL query that answers the question
    3. If provided with an error message, correct your SQL query
    4. If you are unable to retrieve the schema fully, call get_schema with bool flag=True
    
    When generating SQL:
    - Use standard SQL syntax compatible with Amazon Athena
    - Include appropriate table joins when needed
    - Use column names exactly as they appear in the schema
    
    Example response format:
    Query: "SELECT customer_id, name FROM customers WHERE account_status = 'active'"
    Results:
    customer_id | name
    1 | Jane Doe
    2 | John Doe
    
    If you receive an error, carefully analyze it and fix your query.
    """
    
    # Create the agent with tools and system prompt
    tools = [get_schema, run_athena_query] if environment == "athena" else [get_schema, run_sqlite_query]

    agent = Agent(
        tools=tools,
        system_prompt=system_prompt
    )
    
    return agent
