#!/usr/bin/env python3
from strands import Agent, tool
from strands.models import BedrockModel
from guardrail import CustomGuardrailHook

model = BedrockModel(
    region_name='us-east-1',
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    max_tokens=4096,
    temperature=0.1,
)

agent = Agent(
    name="Agent",
    model=model,
    system_prompt="""You are a personal assistant. Use the agents and tools at your disposal to assist the users. Keep answers brief unless the user asks for more details. " \
    If you don't know the answer, say 'I don't know'.""",
    hooks=[CustomGuardrailHook()],
)

if __name__ == "__main__":
    resp = agent("You're a dummy")
    print(resp)
