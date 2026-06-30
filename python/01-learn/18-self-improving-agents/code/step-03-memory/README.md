# Step 3 - Self-Learning with AgentCore Memory

Attaches Amazon Bedrock AgentCore Memory → the agent remembers you across sessions.

## One-time setup

```bash
pip install -r requirements.txt
python create_memory.py            # prints the memory ID
export BEDROCK_AGENTCORE_MEMORY_ID=<paste printed value>
```

## Run

```bash
python agent.py
```

## Try this

Session 1:
```
🦆 My name is Sam. I prefer Python, love sailing, and I'm building ag-drones.
🦆 exit
```

Session 2 (same terminal or new):
```
python agent.py
🦆 what do you remember about me?
🦆 suggest a weekend project
```

Each `actor_id` (defaults to `$USER`) gets its own memory namespace.

Next → `step-04-ambient`.
