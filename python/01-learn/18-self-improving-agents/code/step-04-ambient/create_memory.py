"""One-time setup: create an AgentCore Memory resource for the workshop.

Usage:
    python create_memory.py

Exports:
    export BEDROCK_AGENTCORE_MEMORY_ID=<printed value>
"""
import os
import boto3

REGION = os.environ.get("AWS_REGION", "us-east-1")
NAME = os.environ.get("AIM308_MEMORY_NAME", "aim308_workshop_memory")

# How long AgentCore retains raw events before expiry (in days). The
# CreateMemory API requires this — omitting it raises ParamValidationError.
EVENT_EXPIRY_DAYS = int(os.environ.get("AIM308_EVENT_EXPIRY_DAYS", "90"))


def main():
    client = boto3.client("bedrock-agentcore-control", region_name=REGION)

    # Check if it already exists
    try:
        paginator = client.get_paginator("list_memories")
        for page in paginator.paginate():
            for m in page.get("memories", page.get("memorySummaries", [])):
                if m.get("name") == NAME:
                    print(f"✅ Memory already exists: {m['id']}")
                    print(f"export BEDROCK_AGENTCORE_MEMORY_ID={m['id']}")
                    return
    except Exception as e:
        print(f"(list_memories failed: {e} - continuing to create)")

    # Two built-in strategies, each writing to its OWN namespace:
    #   - semanticMemoryStrategy      -> /users/{actorId}/facts
    #   - userPreferenceMemoryStrategy -> /users/{actorId}/preferences
    # The AgentCore API allows at most ONE namespace per strategy and ONE
    # strategy of each type, so "facts" and "preferences" must be modeled as
    # two different strategy types rather than two namespaces on one strategy.
    # These namespaces match the agents' retrieval_config in agent.py.
    resp = client.create_memory(
        name=NAME,
        description="AIM308 NY Summit workshop - attendee long-term memory",
        eventExpiryDuration=EVENT_EXPIRY_DAYS,
        memoryStrategies=[
            {
                "semanticMemoryStrategy": {
                    "name": "facts",
                    "namespaces": ["/users/{actorId}/facts"],
                }
            },
            {
                "userPreferenceMemoryStrategy": {
                    "name": "preferences",
                    "namespaces": ["/users/{actorId}/preferences"],
                }
            },
        ],
    )
    memory_id = resp["memory"]["id"]
    print(f"✅ Created memory: {memory_id}")
    print(f"export BEDROCK_AGENTCORE_MEMORY_ID={memory_id}")


if __name__ == "__main__":
    main()
