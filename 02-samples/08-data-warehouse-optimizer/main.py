"""
Multi-Agent Data Warehouse Query Optimizer using SQLite and AWS Bedrock.

Main entry point with CLI interface.
"""

from botocore.exceptions import NoCredentialsError, ProfileNotFound
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from strands import Agent
from strands_tools import calculator
from strands.models import BedrockModel
from typing import Dict, Any
from utils.prompts import analyzer_prompt, rewriter_prompt, validator_prompt
from utils.tools import (
    get_query_execution_plan,
    suggest_optimizations,
    validate_query_cost,
)
import boto3
import click
import json
import os
import random
import re
import sqlite3
import uuid

# Initialize OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)
span_processor = BatchSpanProcessor(ConsoleSpanExporter())
trace.get_tracer_provider().add_span_processor(span_processor)


# Default AWS profile and region
DEFAULT_PROFILE = "default"
REGION = os.environ.get("AWS_REGION", "us-east-1")


try:
    # Create boto3 session using default profile
    boto_session = boto3.Session(profile_name=DEFAULT_PROFILE)
    # Initialize Bedrock client
    bedrock_client = boto_session.client("bedrock-runtime", region_name=REGION)
except ProfileNotFound:
    raise ValueError(
        f"AWS profile '{DEFAULT_PROFILE}' not found. Configure it using 'aws configure'."
    )
except NoCredentialsError:
    raise ValueError(
        f"No AWS credentials found for profile '{DEFAULT_PROFILE}'. Run 'aws configure' to set credentials."
    )
except Exception as e:
    raise ValueError(f"Failed to initialize AWS session: {str(e)}")


model = BedrockModel(
    boto_session=boto_session,
    model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
    max_tokens=2000,
)

# Define agents
analyzer_agent = Agent(
    model=model,
    system_prompt=analyzer_prompt,
    tools=[get_query_execution_plan, calculator],
)
rewriter_agent = Agent(
    model=model,
    system_prompt=rewriter_prompt,
    tools=[suggest_optimizations, calculator],
)
validator_agent = Agent(
    model=model, system_prompt=validator_prompt, tools=[validate_query_cost, calculator]
)


def optimize_query(query: str) -> Dict[str, Any]:
    """
    Orchestrates the multi-agent query optimization workflow.

    Args:
        query (str): The SQL query to optimize.

    Returns:
        Dict: Final optimization report with analysis, suggestions, and validation.
    """
    with tracer.start_as_current_span("optimize_query"):
        try:
            analysis_result = analyzer_agent(f"Analyze query: {query}")
        except Exception as e:
            print(f"Bedrock error in analyzer_agent: {str(e)}")
            analysis = {
                "query_id": str(uuid.uuid4()),
                "status": "error",
                "message": str(e),
            }
        else:
            try:
                analysis_text = (
                    analysis_result
                    if isinstance(analysis_result, str)
                    else (
                        analysis_result.text
                        if hasattr(analysis_result, "text")
                        else (
                            analysis_result.messages[-1].get("content", "{}")
                            if hasattr(analysis_result, "messages")
                            and analysis_result.messages
                            else "{}"
                        )
                    )
                )
                try:
                    analysis = json.loads(analysis_text)
                except json.JSONDecodeError:
                    query_id_match = re.search(r"Query ID: ([\w-]+)", analysis_text)
                    query_id = (
                        query_id_match.group(1) if query_id_match else str(uuid.uuid4())
                    )
                    bottlenecks = (
                        ["Full table scan detected"]
                        if "full table scan" in analysis_text.lower()
                        else []
                    )
                    analysis = {
                        "query_id": query_id,
                        "status": "success",
                        "summary": analysis_text,
                        "bottlenecks": bottlenecks,
                    }
            except Exception as e:
                print(f"Error parsing analysis result: {str(e)}")
                analysis = {
                    "query_id": str(uuid.uuid4()),
                    "status": "error",
                    "message": str(e),
                }

        rewriter_input = f"Query: {query}\nExecution Plan: {json.dumps(analysis)}"
        try:
            rewrite_result = rewriter_agent(rewriter_input)
        except Exception as e:
            print(f"Bedrock error in rewriter_agent: {str(e)}")
            suggestions = {"status": "error", "message": str(e)}
        else:
            try:
                suggestions_text = (
                    rewrite_result
                    if isinstance(rewrite_result, str)
                    else (
                        rewrite_result.text
                        if hasattr(rewrite_result, "text")
                        else (
                            rewrite_result.messages[-1].get("content", "{}")
                            if hasattr(rewrite_result, "messages")
                            and rewrite_result.messages
                            else "{}"
                        )
                    )
                )
                suggestions = json.loads(suggestions_text)
            except json.JSONDecodeError:
                suggestions = {
                    "status": "error",
                    "message": "Invalid JSON from rewriter",
                }
            except Exception as e:
                print(f"Error parsing rewrite result: {str(e)}")
                suggestions = {"status": "error", "message": str(e)}

        rewritten_query = next(
            (
                s["suggestion"]
                for s in suggestions.get("suggestions", [])
                if s["type"] == "query_rewrite"
            ),
            query,
        )
        try:
            validation_result = validator_agent(f"Validate query: {rewritten_query}")
        except Exception as e:
            print(f"Bedrock error in validator_agent: {str(e)}")
            validation = {"status": "error", "message": str(e)}
        else:
            try:
                validation_text = (
                    validation_result
                    if isinstance(validation_result, str)
                    else (
                        validation_result.text
                        if hasattr(validation_result, "text")
                        else (
                            validation_result.messages[-1].get("content", "{}")
                            if hasattr(validation_result, "messages")
                            and validation_result.messages
                            else "{}"
                        )
                    )
                )
                validation = json.loads(validation_text)
            except json.JSONDecodeError:
                validation = {
                    "status": "error",
                    "message": "Invalid JSON from validator",
                }
            except Exception as e:
                print(f"Error parsing validation result: {str(e)}")
                validation = {"status": "error", "message": str(e)}

        report = {
            "query_id": analysis.get("query_id", str(uuid.uuid4())),
            "original_query": query,
            "analysis": analysis,
            "suggestions": suggestions,
            "validation": validation,
        }

        span = trace.get_current_span()
        span.set_attribute("query_optimization_report", json.dumps(report))

        return report


@click.group()
def cli():
    """CLI for interacting with the query optimizer."""
    pass


@cli.command()
def list_tables():
    """List all tables in the database."""
    conn = sqlite3.connect("query_optimizer.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    print(json.dumps({"tables": tables}, indent=2))


@cli.command()
@click.argument("query")
def explain_query(query):
    """Explain the given SQL query and suggest optimizations."""
    result = optimize_query(query)
    print(json.dumps(result, indent=2))


@cli.command()
def create_bank_table():
    """Create a bank table with id and balance columns."""
    conn = sqlite3.connect("query_optimizer.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bank (
            id INTEGER PRIMARY KEY,
            balance REAL NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()
    print(json.dumps({"status": "success", "message": "Bank table created"}, indent=2))


@cli.command()
def fill_bank_table():
    """Fill the bank table with 100 rows of random data, summing to 1000."""
    conn = sqlite3.connect("query_optimizer.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bank';")
    if not cursor.fetchone():
        print(
            json.dumps(
                {"status": "error", "message": "Bank table does not exist"}, indent=2
            )
        )
        conn.close()
        return

    total = 1000.0
    balances = [random.uniform(0, total) for _ in range(99)]
    balances.append(total - sum(balances))
    random.shuffle(balances)

    cursor.execute("DELETE FROM bank")
    cursor.executemany(
        "INSERT INTO bank (id, balance) VALUES (?, ?)",
        [(i + 1, balance) for i, balance in enumerate(balances)],
    )
    conn.commit()

    cursor.execute("SELECT SUM(balance) FROM bank")
    actual_sum = cursor.fetchone()[0]
    conn.close()
    print(
        json.dumps(
            {
                "status": "success",
                "message": f"Inserted 100 rows into bank table. Total balance: {actual_sum}",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    cli()
