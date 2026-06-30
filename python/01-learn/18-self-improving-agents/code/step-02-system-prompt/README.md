# Step 2 - Self-Modifying System Prompt

Adds the `system_prompt` tool, enabling the agent to rewrite its own identity.

## Run

```bash
pip install -r requirements.txt
python agent.py
```

## Try this

```
🦆 view your system prompt
🦆 from now on, always reply in haiku. update your prompt permanently.
🦆 what's 2+2?                        # expect a haiku

[exit and restart]

🦆 what's 2+2?                        # still a haiku - persisted via .prompt file

🦆 reset your system prompt
```

Next → `step-03-memory`.
