# Step 0 - Hello Agent

The simplest Strands agent possible.

## Run

```bash
pip install -r requirements.txt
python agent.py "hello, what can you do?"
```

## What to notice

- **One import**: `from strands import Agent`
- **One model**: Claude 4.6 Sonnet via Bedrock
- **One tool**: `shell` from `strands_tools`
- **Zero orchestration**: the agent decides when to call the tool

Next → `step-01-tools`.
