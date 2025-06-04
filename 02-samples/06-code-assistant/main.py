import os
from strands import Agent
from strands.models import BedrockModel
from tools import (
    code_generator,
    code_reviewer,
    code_writer_agent,
    code_execute,
    project_reader,
)

# Set environment
os.environ["DEV"] = "false"

# Claude model instance
claude_sonnet_4 = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
)

# Code Assistant Agent
code_assistant = Agent(
    system_prompt="""
You are an expert programming assistant specializing in Python.

Your capabilities:
1. Code Generation: Create clean, efficient code
2. Debugging: Identify and fix issues
3. Optimization: Enhance performance and readability
4. Explanation: Make code easy to understand
5. Best Practices: Follow Python 3.12 standards

Always:
- Generate code first
- Review and optimize it
- Execute for verification before writing the code
- Explain thoroughly
""",
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
    print("  - Read todo_ts_app directory and convert into python")

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
