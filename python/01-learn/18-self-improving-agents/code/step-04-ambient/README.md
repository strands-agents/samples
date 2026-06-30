# Step 4 - Autonomous: Ambient Mode + Scheduler

Adds two forms of autonomy:

1. **Ambient mode** - background thread keeps working during idle time
2. **Scheduler** - cron-style recurring jobs

## Run ambient mode

```bash
pip install -r requirements.txt
export BEDROCK_AGENTCORE_MEMORY_ID=<your memory id>
python agent.py
```

Ask a deep question, then wait 20 seconds. Watch 🌙 messages stream in.

## Run scheduler (separate terminal)

```bash
python scheduler.py             # fires every 5 min, writes journal.md
```

Override interval:

```bash
AIM308_SCHEDULE_MIN=1 python scheduler.py
```

Next → `step-05-deploy`.
