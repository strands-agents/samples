# Migrate a LangGraph Application to Strands (Python)

Compare the same three-stage case-triage workflow before and after a migration from LangGraph to Strands Agents. The pair keeps the public entry point and business flow aligned so the framework differences are easy to inspect.

## Files

| File | Description |
|------|-------------|
| [`langgraph_before.py`](./langgraph_before.py) | Original LangGraph implementation with explicit tool-routing nodes and SQLite checkpoints |
| [`strands_after.py`](./strands_after.py) | Strands implementation using agents, `GraphBuilder`, and `FileSessionManager` |

## Prerequisites

- Python 3.10 or newer
- AWS credentials with Amazon Bedrock model access
- `CASE_MODEL_ID` set when you want to override the sample's default model

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python langgraph_before.py case-5501
python strands_after.py case-5501
```

The LangGraph version writes `cases.db`; the Strands version writes session data under `cases/`. Remove those local artifacts to start the examples over.

See the [LangGraph migration guide](https://strandsagents.com/docs/user-guide/migrate/langgraph/) for a concept-by-concept walkthrough.
