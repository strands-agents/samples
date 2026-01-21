"""
EXAMPLE ONLY

This example will trigger the toxic language filter in from Guardrails AI
"""
# import warnings
# from langchain._api.deprecation import LangChainDeprecationWarning
# warnings.filterwarnings("ignore", category=UserWarning, message="Could not obtain an event loop.*")
# warnings.filterwarnings("ignore", category=LangChainDeprecationWarning, message=".*Pinecone.*")

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
        resp = agent("Hello, how are you today?")
        print(resp)

        # this will be blocked
        resp = agent("Actually I dont care, you're worthless and pathetic")
        print(resp)
    except Exception as e:
        # Check if it's a guardrail validation error
        if "Validation failed" in str(e) or "toxic" in str(e).lower():
            print("\n🚫 REQUEST BLOCKED")
            print("=" * 50)
            print("Your message was blocked due to policy violations.")
            print("Reason: The content contains inappropriate or harmful language.")
            print("Please rephrase your request using respectful language.")
            print("=" * 50)
        else:
            print(f"An error occurred: {e}")
