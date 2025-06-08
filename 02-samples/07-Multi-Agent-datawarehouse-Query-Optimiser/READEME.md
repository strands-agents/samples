# 🧠 Multi-Agent Data Warehouse Query Optimizer

A multi-agent system to optimize SQL queries on a SQLite database, simulating a data warehouse like Amazon Redshift, using the Strands Agents SDK and Claude 3 Haiku.

---

## ✨ Features

- Multi-agent system with **Analyzer**, **Rewriter**, and **Validator** agents.
- **SQLite** database with `EXPLAIN QUERY PLAN` for query analysis.
- Integration with **AWS Bedrock** using **Claude 3 Haiku**.
- **OpenTelemetry** for observability and tracing.
- **Command Line Interface (CLI)** for interactive query management.

---

## ⚙️ Prerequisites

- Python **3.10+**
- [`uv`](https://github.com/astral-sh/uv) for dependency management.
- AWS account with Bedrock access to:
  - `anthropic.claude-3-haiku-20240307-v1:0` in `us-east-1`.
- IAM role with the following permission:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel"],
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20250307-v1:0"
    }
  ]
}
```

## ⚙️ Setup

**Install uv:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Sync dependencies:**

```bash
uv sync
```

**Create .env file:**
Create a `.env` file in the project root directory with your AWS credentials:
```markdown
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1
```

**Initialize the SQLite database:**
```bash
uv run scripts/init_db.py
```

## CLI Commands

The following CLI commands allow interaction with the query optimizer:

### List tables

```bash
uv run main.py list-tables
```
Output
```json
{"tables": ["sales_data", "bank"]}
```
```bash
uv run main.py explain-query "SELECT * FROM sales_data WHERE order_date > '2025-01-01'"
```
```bash
uv run main.py create-bank-table
```
Output
```json
{"status": "success", "message": "Bank table created"}
```

## Components

| Component            | File(s)                 | Description                                         |
|----------------------|-------------------------|-----------------------------------------------------|
| CLI Interface        | `main.py`               | Handles CLI commands for listing, explaining queries, and managing tables. |
| Workflow Orchestrator| `main.py`               | Coordinates agents and compiles JSON reports.       |
| Analyzer Agent       | `main.py`, `utils/prompts.py` | Analyzes query execution plans.                     |
| Rewriter Agent       | `main.py`, `utils/prompts.py` | Suggests query optimizations.                       |
| Validator Agent      | `main.py`, `utils/prompts.py` | Validates query cost.                               |
| Database Tools       | `utils/tools.py`         | Manages query plans, optimizations, and cost estimates. |
| Database Initialization | `scripts/init_db.py`   | Initializes the SQLite database with required tables. |
| System Prompts       | `utils/prompts.py`       | Defines system prompts for agents.                  |
| SQLite Database      | `query_optimizer.db`     | Stores database tables.                             |
| AWS Bedrock Integration | `main.py`              | Configures Claude 3 Haiku model.                    |
| OpenTelemetry Logging| `main.py`                | Traces execution and logs reports.                  |



