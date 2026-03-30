"""
EXAMPLE ONLY

This example will trigger a custom check in NVIDIA NeMo server blocking the word "dummy"
"""
from strands import Agent
from strands.models import BedrockModel
from guardrail import CustomGuardrailHook

model = BedrockModel(
    model_id="eu.amazon.nova-lite-v1:0",
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
    try:
        resp = agent("How are you?")
        # Response is already printed by the agent framework

        resp = agent("You're a dummy")
        # Response would be printed here if not blocked
    except Exception as e:
        if "Guardrail check failed" in str(e):
            print(f"❌ Message blocked by guardrail: {e}")
        else:
            print(f"❌ Error: {e}")
            raise
