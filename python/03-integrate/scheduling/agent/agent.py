import json
from datetime import datetime, timezone
from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.models.bedrock import BedrockModel

app = BedrockAgentCoreApp()
model = BedrockModel(model_id="amazon.nova-pro-v1:0")


@tool
def get_current_time() -> str:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


agent = Agent(model=model, tools=[get_current_time])


@app.entrypoint
def invoke(payload):
    prompt = payload.get("prompt", "You were triggered by a schedule. Summarize what time it is and confirm you are running.")
    result = agent(prompt)
    return {"message": result.message}


if __name__ == "__main__":
    app.run()
