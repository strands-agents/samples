"""AIM308 - Step 0: Hello Agent.

The minimum viable Strands agent. Claude 4.6 Sonnet + one tool (shell).
"""
import sys
from strands import Agent
from strands_tools import shell

MODEL_ID = "global.anthropic.claude-opus-4-8"


def main():
    agent = Agent(
        model=MODEL_ID,
        tools=[shell],
        system_prompt=(
            "You are a helpful assistant. "
            "Use the shell tool when useful. Be concise."
        ),
    )
    query = " ".join(sys.argv[1:]) or "Hello, introduce yourself in one sentence."
    agent(query)


if __name__ == "__main__":
    main()
