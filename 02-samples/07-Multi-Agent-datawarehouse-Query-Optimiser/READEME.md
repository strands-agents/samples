# Multi-Agent Data Warehouse Query Optimizer (SQLite)

 

This example demonstrates a multi-agent system using the Strands Agents SDK to optimize SQL queries on a SQLite database, simulating a data warehouse environment like Amazon Redshift. Three agents (Analyzer, Rewriter, Validator) collaborate to analyze query execution plans, suggest optimizations, and validate performance improvements.

 

## Features
- Uses SQLite with `EXPLAIN QUERY PLAN` to simulate query analysis.
- Integrates AWS Bedrock with Claude 3 Haiku for agent intelligence.
- Logs agent actions with OpenTelemetry for observability.
- Produces a JSON report with query analysis, optimization suggestions, and validation results.

 

## Prerequisites
- Python 3.8+
- AWS account with Bedrock access to `anthropic.claude-3-haiku-<id>-v1:0` in `us-east-1`.
- IAM role/user with permissions:
  ```json
  {
      "Version": "2012-10-17",
      "Statement": [
          {
              "Effect": "Allow",
              "Action": [
                  "bedrock:InvokeModel",
                  "bedrock:InvokeModelWithResponseStream"
              ],
              "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-<id>-v1:0"
          }
      ]
  }