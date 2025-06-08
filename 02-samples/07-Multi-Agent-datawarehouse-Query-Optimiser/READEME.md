Multi-Agent Data Warehouse Query Optimizer
A multi-agent system to optimize SQL queries on a SQLite database, simulating a data warehouse like Amazon Redshift, using Strands Agents SDK and Claude 3 Haiku.
Features

Multi-agent system with Analyzer, Rewriter, and Validator agents.
SQLite database with EXPLAIN QUERY PLAN for query analysis.
AWS Bedrock integration with Claude 3 Haiku.
OpenTelemetry for observability.
CLI for interactive query management.

Prerequisites

Python 3.10+
uv for dependency management.
AWS account with Bedrock access to anthropic.claude-3-haiku-20240307-v1:0 in us-east-1.
IAM role with:{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["bedrock:InvokeModel"],
            "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20250307-v1:0"
        }
    ]
}



Setup

Install uv:curl -LsSf https://astral.sh/uv/install.sh | sh


Sync dependencies:uv sync


Create .env:AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1


Initialize database:uv run scripts/init_db.py


Run CLI commands:uv run main.py list-tables
uv run main.py explain-query "SELECT * FROM sales_data WHERE order_date > '2025-01-01'"
uv run main.py create-bank-table
uv run main.py fill-bank-table



CLI Commands

List tables:uv run main.py list-tables

Output: {"tables": ["sales_data", "bank"]}
Explain query:uv run main.py explain-query "SELECT * FROM sales_data WHERE order_date > '2025-01-01'"

Output: JSON report with analysis, suggestions, and validation.
Create bank table:uv run main.py create-bank-table

Output: {"status": "success", "message": "Bank table created"}
Fill bank table:uv run main.py fill-bank-table

Output: {"status": "success", "message": "Inserted 100 rows into bank table. Total balance: 1000.0"}

Architecture
Diagram
+-----------------------+
|       CLI Interface   |
| - List tables         |
| - Explain query       |
| - Create bank table   |
| - Fill bank table     |
+-----------------------+
           |
           v
+-----------------------+
|    Workflow Orchestrator  |
| - Coordinates agents  |
| - Compiles JSON report |
+-----------------------+
           |
           v
+-----------------------+
|       Agents          |
| - Analyzer Agent      |
| - Rewriter Agent      |
| - Validator Agent     |
+-----------------------+
           |
           v
+-----------------------+
|       Tools           |
| - get_query_execution_plan |
| - suggest_optimizations |
| - validate_query_cost |
+-----------------------+
           |
           v
+-----------------------+
|      SQLite Database  |
| - sales_data table    |
| - bank table (CLI)    |
+-----------------------+
           |
           v
+-----------------------+
|    AWS Bedrock        |
| - Claude 3 Haiku      |
+-----------------------+
           |
           v
+-----------------------+
|    OpenTelemetry      |
| - Traces query execution |
| - Logs JSON reports   |
+-----------------------+

Components



Component
File
Description



CLI Interface
main.py
Handles commands for listing tables, explaining queries, creating/filling tables.


Workflow Orchestrator
main.py
Coordinates agents via optimize_query, compiles JSON report.


Analyzer Agent
main.py, utils/prompts.py
Analyzes query execution plans using get_query_execution_plan.


Rewriter Agent
main.py, utils/prompts.py
Suggests optimizations using suggest_optimizations.


Validator Agent
main.py, utils/prompts.py
Validates query cost using validate_query_cost.


Database Tools
utils/tools.py
Manages SQLite query plans, optimizations, and cost estimation.


Database Initialization
scripts/init_db.py
Initializes SQLite database with sales_data table as a prerequisite.


System Prompts
utils/prompts.py
Defines prompts for Analyzer, Rewriter, and Validator agents.


SQLite Database
query_optimizer.db
Stores sales_data and user-created tables (e.g., bank).


AWS Bedrock
main.py
Configures Claude 3 Haiku with non-streaming API.


OpenTelemetry
main.py
Traces execution and logs JSON reports.

License
MIT License.
