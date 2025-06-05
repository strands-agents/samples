"""

Multi-Agent Data Warehouse Query Optimizer using SQLite and AWS Bedrock.



This script implements a multi-agent system to optimize SQL queries on a SQLite database,

simulating a data warehouse like Amazon Redshift. It uses the Strands Agents SDK with

Claude 3 Haiku for query analysis, optimization suggestions, and performance validation.

"""

import sqlite3
import json
import uuid
import boto3
import re
import os
from typing import List, Dict, Any
from strands import Agent, tool
from strands_tools import calculator
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from dotenv import load_dotenv
from strands.models import BedrockModel



# Load environment variables from .env

load_dotenv()


# Initialize OpenTelemetry for observability

trace.set_tracer_provider(TracerProvider())

tracer = trace.get_tracer(__name__)

span_processor = BatchSpanProcessor(ConsoleSpanExporter())

trace.get_tracer_provider().add_span_processor(span_processor)





# Initialize SQLite database

def init_db():

    """Initialize SQLite database with sample sales_data table."""

    conn = sqlite3.connect("query_optimizer.db")

    cursor = conn.cursor()

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS sales_data (

            order_id INTEGER PRIMARY KEY,

            customer_id INTEGER,

            order_date TEXT,

            amount REAL

        )

    """)

    # Insert sample data

    cursor.executemany(

        "INSERT OR IGNORE INTO sales_data (order_id, customer_id, order_date, amount) "

        "VALUES (?, ?, ?, ?)",

        [

            (1, 101, "2025-01-01", 100.50),

            (2, 102, "2025-01-02", 200.75),

            (3, 101, "2025-01-03", 150.25)

        ]

    )

    conn.commit()

    conn.close()





# Tool 1: Query SQLite for execution plan

@tool

def get_query_execution_plan(query: str) -> str:

    """

    Retrieves the execution plan for a given SQLite query using EXPLAIN QUERY PLAN.



    Args:

        query (str): The SQL query to analyze.



    Returns:

        str: JSON string with execution plan details or error message.

    """

    with tracer.start_as_current_span("get_query_execution_plan"):

        try:

            conn = sqlite3.connect("query_optimizer.db")

            cursor = conn.cursor()

            cursor.execute(f"EXPLAIN QUERY PLAN {query}")

            plan = cursor.fetchall()

            conn.close()

            return json.dumps({

                'status': 'success',

                'query_id': str(uuid.uuid4()),

                'execution_plan': plan,

                'bottlenecks': analyze_plan(plan)

            })

        except sqlite3.Error as e:

            return json.dumps({

                'status': 'error',

                'message': str(e)

            })





# Helper function to identify bottlenecks

def analyze_plan(plan: List) -> List[str]:

    """Identify bottlenecks in SQLite execution plan."""

    bottlenecks = []

    for step in plan:

        detail = step[3].lower()

        if 'scan' in detail and 'index' not in detail:

            bottlenecks.append("Full table scan detected")

        if 'temporary table' in detail:

            bottlenecks.append("Use of temporary table detected")

    return bottlenecks





# Tool 2: Suggest query or schema optimizations

@tool

def suggest_optimizations(query: str, execution_plan: str) -> str:

    """

    Suggests query rewrites or schema changes based on the query and execution plan.



    Args:

        query (str): The original SQL query.

        execution_plan (str): JSON string of the execution plan.



    Returns:

        str: JSON string with suggested query rewrites or schema changes.

    """

    with tracer.start_as_current_span("suggest_optimizations"):

        try:

            plan_data = json.loads(execution_plan)

            suggestions = []

            

            if 'full table scan' in str(plan_data.get('bottlenecks', [])):

                suggestions.append({

                    'type': 'schema_change',

                    'suggestion': 'Create index on filtered columns (e.g., customer_id, order_date)'

                })

                suggestions.append({

                    'type': 'query_rewrite',

                    'suggestion': f"Use selective filters: "

                                  f"{query.replace('SELECT *', 'SELECT order_id, customer_id')}"

                })

            if 'temporary table' in str(plan_data.get('bottlenecks', [])):

                suggestions.append({

                    'type': 'query_rewrite',

                    'suggestion': 'Simplify joins/subqueries to avoid temporary tables'

                })

                

            return json.dumps({

                'status': 'success',

                'suggestions': suggestions

            })

        except Exception as e:

            return json.dumps({

                'status': 'error',

                'message': str(e)

            })





# Tool 3: Validate query cost using EXPLAIN QUERY PLAN

@tool

def validate_query_cost(query: str) -> str:

    """

    Validates the cost of a rewritten query using SQLite's EXPLAIN QUERY PLAN.



    Args:

        query (str): The rewritten SQL query to validate.



    Returns:

        str: JSON string with estimated query cost or error message.

    """

    with tracer.start_as_current_span("validate_query_cost"):

        try:

            conn = sqlite3.connect("query_optimizer.db")

            cursor = conn.cursor()

            cursor.execute(f"EXPLAIN QUERY PLAN {query}")

            plan = cursor.fetchall()

            conn.close()

            

            cost = estimate_cost(plan)

            return json.dumps({

                "status": "success",

                "cost": cost,

                "message": f"Estimated query cost: {cost}"

            })

        except sqlite3.Error as e:

            return json.dumps({

                "status": "error",

                "message": str(e)

            })





# Helper function to estimate query cost

def estimate_cost(plan: List) -> float:

    """Estimate query cost from SQLite EXPLAIN QUERY PLAN."""

    total_cost = 0.0

    for step in plan:

        detail = step[3].lower()

        if 'scan' in detail and 'index' not in detail:

            total_cost += 100.0  # High cost for full table scans

        elif 'index' in detail:

            total_cost += 10.0   # Lower cost for index usage

    return total_cost





# System prompts for agents

analyzer_prompt = """

You are an expert SQLite query performance analyzer. Your role is to:

1. Use the get_query_execution_plan tool to retrieve and analyze SQLite query execution plans.

2. Identify bottlenecks such as full table scans or temporary table usage.

3. Return a JSON object with the query ID, execution plan summary, and identified bottlenecks.

Example output:

{

  "query_id": "<uuid>",

  "status": "success",

  "summary": "Full table scan detected on sales_data table",

  "bottlenecks": ["Full table scan detected"]

}

"""



rewriter_prompt = """

You are an expert SQL query optimizer for SQLite. Your role is to:

1. Use the suggest_optimizations tool to propose query rewrites or schema changes based on the execution plan.

2. Return a JSON object with the original query and suggested optimizations.

Example output:

{

  "status": "success",

  "original_query": "<query>",

  "suggestions": [

    {"type": "schema_change", "suggestion": "Create an index on order_date"},

    {"type": "query_rewrite", "suggestion": "SELECT order_id, customer_id FROM sales_data WHERE order_date > '2025-01-01'"}

  ]

}

"""



validator_prompt = """

You are a SQLite query validator. Your role is to:

1. Use the validate_query_cost tool to estimate the cost of rewritten queries using SQLite's EXPLAIN QUERY PLAN.

2. Return a JSON object with the query, estimated cost, and validation summary.

Example output:

{

  "status": "success",

  "query": "<query>",

  "cost": 10.0,

  "message": "Estimated query cost: 10.0"

}

"""





# Define the Bedrock model with access and secret keys from .env

aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")

aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

if not aws_access_key or not aws_secret_key:

    raise ValueError("AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set in .env")

boto_session = boto3.Session(

    aws_access_key_id=aws_access_key,

    aws_secret_access_key=aws_secret_key,

    region_name="us-east-1"

)

model = BedrockModel(

    boto_session=boto_session,

    model_id="anthropic.claude-3-haiku-20240307-v1:0",

    max_tokens=4000)





# Define the agents

analyzer_agent = Agent(

    model=model,

    system_prompt=analyzer_prompt,

    tools=[get_query_execution_plan, calculator]

)



rewriter_agent = Agent(

    model=model,

    system_prompt=rewriter_prompt,

    tools=[suggest_optimizations, calculator]

)



validator_agent = Agent(

    model=model,

    system_prompt=validator_prompt,

    tools=[validate_query_cost, calculator]

)





# Main function to orchestrate the multi-agent workflow

def optimize_query(query: str) -> Dict[str, Any]:

    """

    Orchestrates the multi-agent query optimization workflow.



    Args:

        query (str): The SQL query to optimize.



    Returns:

        Dict: Final optimization report with analysis, suggestions, and validation.

    """

    with tracer.start_as_current_span("optimize_query"):

        # Initialize database

        init_db()

        

        # Step 1: Analyze query execution plan

        try:

            analysis_result = analyzer_agent(f"Analyze query: {query}")

        except Exception as e:

            print(f"Bedrock error in analyzer_agent: {str(e)}")

            analysis = {"query_id": str(uuid.uuid4()), "status": "error", "message": str(e)}

        else:

            try:

                # Check if result is a string (direct text output)

                if isinstance(analysis_result, str):

                    analysis_text = analysis_result

                # Check for 'text' attribute

                elif hasattr(analysis_result, 'text'):

                    analysis_text = analysis_result.text

                # Check for 'messages' attribute

                elif hasattr(analysis_result, 'messages') and analysis_result.messages:

                    analysis_text = analysis_result.messages[-1].get('content', '{}')

                else:

                    analysis_text = '{}'

                

                # Try parsing as JSON; if it fails, extract info from text

                try:

                    analysis = json.loads(analysis_text)

                except json.JSONDecodeError:

                    # Parse text manually (based on observed output)

                    query_id_match = re.search(r"Query ID: ([\w-]+)", analysis_text)

                    query_id = query_id_match.group(1) if query_id_match else str(uuid.uuid4())

                    bottlenecks = []

                    if "full table scan" in analysis_text.lower():

                        bottlenecks.append("Full table scan detected")

                    analysis = {

                        "query_id": query_id,

                        "status": "success",

                        "summary": analysis_text,

                        "bottlenecks": bottlenecks

                    }

            except Exception as e:

                print(f"Error parsing analysis result: {str(e)}")

                analysis = {"query_id": str(uuid.uuid4()), "status": "error", "message": str(e)}



        # Step 2: Suggest optimizations

        rewriter_input = f"Query: {query}\nExecution Plan: {json.dumps(analysis)}"

        try:

            rewrite_result = rewriter_agent(rewriter_input)

        except Exception as e:

            print(f"Bedrock error in rewriter_agent: {str(e)}")

            suggestions = {"status": "error", "message": str(e)}

        else:

            try:

                if isinstance(rewrite_result, str):

                    suggestions_text = rewrite_result

                elif hasattr(rewrite_result, 'text'):

                    suggestions_text = rewrite_result.text

                elif hasattr(rewrite_result, 'messages') and rewrite_result.messages:

                    suggestions_text = rewrite_result.messages[-1].get('content', '{}')

                else:

                    suggestions_text = '{}'

                

                try:

                    suggestions = json.loads(suggestions_text)

                except json.JSONDecodeError:

                    suggestions = {"status": "error", "message": "Invalid JSON from rewriter"}

            except Exception as e:

                print(f"Error parsing rewrite result: {str(e)}")

                suggestions = {"status": "error", "message": str(e)}



        # Step 3: Validate rewritten query

        rewritten_query = next(

            (s['suggestion'] for s in suggestions.get('suggestions', []) if s['type'] == 'query_rewrite'),

            query

        )

        try:

            validation_result = validator_agent(f"Validate query: {rewritten_query}")

        except Exception as e:

            print(f"Bedrock error in validator_agent: {str(e)}")

            validation = {"status": "error", "message": str(e)}

        else:

            try:

                if isinstance(validation_result, str):

                    validation_text = validation_result

                elif hasattr(validation_result, 'text'):

                    validation_text = validation_result.text

                elif hasattr(validation_result, 'messages') and validation_result.messages:

                    validation_text = validation_result.messages[-1].get('content', '{}')

                else:

                    validation_text = '{}'

                

                try:

                    validation = json.loads(validation_text)

                except json.JSONDecodeError:

                    validation = {"status": "error", "message": "Invalid JSON from validator"}

            except Exception as e:

                print(f"Error parsing validation result: {str(e)}")

                validation = {"status": "error", "message": str(e)}



        # Compile final report

        report = {

            'query_id': analysis.get('query_id', str(uuid.uuid4())),

            'original_query': query,

            'analysis': analysis,

            'suggestions': suggestions,

            'validation': validation

        }

        

        # Log report with OpenTelemetry

        span = trace.get_current_span()

        span.set_attribute("query_optimization_report", json.dumps(report))

        

        return report

if __name__ == "__main__":

    sample_query = "SELECT * FROM sales_data WHERE order_date > '2025-01-01'"

    try:

        result = optimize_query(sample_query)

        print(json.dumps(result, indent=2))

    except Exception as e:

        print(f"Error during optimization: {str(e)}")