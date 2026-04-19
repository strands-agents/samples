import os
from strands import Agent
from strands.models import BedrockModel
from utils.tools import (
    code_generator,
    code_reviewer,
    code_writer_agent,
    code_execute,
    project_reader,
)
from utils.prompts import CODE_ASSISTANT_PROMPT

# Show rich UI for tools in CLI
os.environ["STRANDS_TOOL_CONSOLE_MODE"] = "enabled"

# Claude model instance
claude_sonnet_4 = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
)

# Code Assistant Agent
code_assistant = Agent(
    system_prompt=CODE_ASSISTANT_PROMPT,
    model=claude_sonnet_4,
    tools=[
        project_reader,
        code_generator,
        code_reviewer,
        code_writer_agent,
        code_execute,
    ],
)
# Example usage
if __name__ == "__main__":
    print("\n💻 Code Assistant Agent 💻\n")
    print("This agent helps with programming tasks")
    print("Type your code question or task below or 'exit' to quit.\n")
    print("Example commands:")
    print("  - Run: print('Hello, World!')")
    print(
        "  - Explain: def fibonacci(n): a,b=0,1; for _ in range(n): a,b=b,a+b; return a"
    )
    print("  - Create a Python script that sorts a list")
    print("  - Read sample_ts_app directory and convert into python")

    # Interactive loop
    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() == "exit":
                print("\nGoodbye! 👋")
                break

            # Process the input as a coding question/task
            code_assistant(user_input)
        except KeyboardInterrupt:
            print("\n\nExecution interrupted. Exiting...")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            print("Please try asking a different question.")
