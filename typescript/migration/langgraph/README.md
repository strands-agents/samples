# Migrate a LangGraph Application to Strands (TypeScript)

Compare the same three-stage case-triage workflow before and after a migration from LangGraph.js to the Strands Agents TypeScript SDK. Both implementations preserve the public entry point and business flow for a direct framework comparison.

## Projects

| Project | Description |
|---------|-------------|
| [`langgraph-before`](./langgraph-before/) | Original LangGraph.js implementation with explicit tool routing and SQLite checkpoints |
| [`strands-after`](./strands-after/) | Strands implementation using agents, `Graph`, and `SessionManager` |

## Prerequisites

- Node.js 22 or newer
- AWS credentials with Amazon Bedrock model access
- `AWS_REGION` configured
- `CASE_MODEL_ID` set when you want to override the sample's default model

## Run

Run each project independently:

```bash
cd langgraph-before
npm install
npm run dev -- case-5501

cd ../strands-after
npm install
npm run dev -- case-5501
```

The LangGraph version writes `cases.db`; the Strands version writes session data under `cases/`. Remove those local artifacts to start the examples over.

See the [LangGraph migration guide](https://strandsagents.com/docs/user-guide/migrate/langgraph/) for a concept-by-concept walkthrough.
