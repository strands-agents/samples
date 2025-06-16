"""
SQLite database tools for query optimization.
"""

import sqlite3
import json
import uuid
from typing import List
from strands import tool
from opentelemetry import trace


@tool
def get_query_execution_plan(query: str) -> str:
    """
    Retrieves the execution plan for a given SQLite query using EXPLAIN QUERY PLAN.

    Args:
        query (str): The SQL query to analyze.

    Returns:
        str: JSON string with execution plan details or error message.
    """
    with trace.get_tracer(__name__).start_as_current_span("get_query_execution_plan"):
        try:
            conn = sqlite3.connect("query_optimizer.db")
            cursor = conn.cursor()
            cursor.execute(f"EXPLAIN QUERY PLAN {query}")
            plan = cursor.fetchall()
            conn.close()
            return json.dumps(
                {
                    "status": "success",
                    "query_id": str(uuid.uuid4()),
                    "execution_plan": plan,
                    "bottlenecks": analyze_plan(plan),
                }
            )
        except sqlite3.Error as e:
            return json.dumps({"status": "error", "message": str(e)})


def analyze_plan(plan: List) -> List[str]:
    """Identify bottlenecks in SQLite execution plan."""
    bottlenecks = []
    for step in plan:
        detail = step[3].lower()
        if "scan" in detail and "index" not in detail:
            bottlenecks.append("Full table scan detected")
        if "temporary table" in detail:
            bottlenecks.append("Use of temporary table detected")
    return bottlenecks


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
    with trace.get_tracer(__name__).start_as_current_span("suggest_optimizations"):
        try:
            plan_data = json.loads(execution_plan)
            suggestions = []
            if "full table scan" in str(plan_data.get("bottlenecks", [])):
                suggestions.append(
                    {
                        "type": "schema_change",
                        "suggestion": "Create index on filtered columns (e.g., customer_id, order_date)",
                    }
                )
                suggestions.append(
                    {
                        "type": "query_rewrite",
                        "suggestion": f"Use selective filters: "
                        f"{query.replace('SELECT *', 'SELECT order_id, customer_id')}",
                    }
                )
            if "temporary table" in str(plan_data.get("bottlenecks", [])):
                suggestions.append(
                    {
                        "type": "query_rewrite",
                        "suggestion": "Simplify joins/subqueries to avoid temporary tables",
                    }
                )
            return json.dumps({"status": "success", "suggestions": suggestions})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})


@tool
def validate_query_cost(query: str) -> str:
    """
    Validates the cost of a rewritten query using SQLite's EXPLAIN QUERY PLAN.

    Args:
        query (str): The rewritten SQL query to validate.

    Returns:
        str: JSON string with estimated query cost or error message.
    """
    with trace.get_tracer(__name__).start_as_current_span("validate_query_cost"):
        try:
            conn = sqlite3.connect("query_optimizer.db")
            cursor = conn.cursor()
            cursor.execute(f"EXPLAIN QUERY PLAN {query}")
            plan = cursor.fetchall()
            conn.close()
            cost = estimate_cost(plan)
            return json.dumps(
                {
                    "status": "success",
                    "cost": cost,
                    "message": f"Estimated query cost: {cost}",
                }
            )
        except sqlite3.Error as e:
            return json.dumps({"status": "error", "message": str(e)})


def estimate_cost(plan: List) -> float:
    """Estimate query cost from SQLite EXPLAIN QUERY PLAN."""
    total_cost = 0.0
    for step in plan:
        detail = step[3].lower()
        if "scan" in detail and "index" not in detail:
            total_cost += 100.0
        elif "index" in detail:
            total_cost += 10.0
    return total_cost
