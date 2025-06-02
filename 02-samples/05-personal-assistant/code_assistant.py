import os
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import python_repl, editor, shell, journal
from constants import SESSION_ID

# Show rich UI for tools in CLI
os.environ["STRANDS_TOOL_CONSOLE_MODE"] = "enabled"


@tool
def code_assistant(query: str) -> str:
    """
    Coding assistant agent
    Args:
        query: A request to the coding assistant

    Returns:
        Output from interaction
    """
    response = agent(query)
    print("\n\n")
    return response


system_prompt = """You are a software expert and coder. Write, debug, test, and iterate on software"""

model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
)

agent = Agent(
    model=model,
    system_prompt=system_prompt,
    tools=[python_repl, editor, shell, journal],
    trace_attributes={"session.id": SESSION_ID},
)


if __name__ == "__main__":
    print("=======================================================================")
    print("💻  WELCOME TO YOUR PERSONAL CODING ASSISTANT  💻")
    print("=======================================================================")
    print("🚀 I'm your expert software developer ready to help with:")
    print("   🐍 Python programming and debugging")
    print("   📝 Code writing and optimization")
    print("   🔧 Testing and error fixing")
    print("   📁 File management and editing")
    print("   🖥️  Shell commands and system operations")
    print("   📋 Project documentation and notes")
    print()
    print("🛠️  Available Tools:")
    print("   • Python REPL - Run and test Python code")
    print("   • Code Editor - Create and modify files")
    print("   • Shell Access - Execute system commands")
    print("   • Journal - Document progress and notes")
    print()
    print("💡 Tips:")
    print("   • Be specific about your coding requirements")
    print("   • I'll test code before providing solutions")
    print("   • Ask for explanations, best practices, or optimizations")
    print("   • Try: 'Create a Python script for...' or 'Debug this code...'")
    print()
    print("🚪 Type 'exit' to quit anytime")
    print("=======================================================================")
    print()

    # Initialize the coding assistant
    try:
        print("✅ Coding Assistant initialized successfully!")
        print()
    except Exception as e:
        print(f"❌ Error initializing Coding Assistant: {str(e)}")
        print("🔧 Please check your configuration and try again.")
    # Run the agent in a loop for interactive conversation
    while True:
        try:
            user_input = input("👨‍💻 You: ").strip()

            if not user_input:
                print("💭 Please describe your coding task or type 'exit' to quit")
                continue
            if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                print()
                print("=======================================================")
                print("👋 Thanks for coding with me!")
                print("🎉 Happy coding and debugging!")
                print("💻 Keep building amazing things!")
                print("=======================================================")
                break
            print("🤖 CodingBot: ", end="")
            response = code_assistant(user_input)

        except KeyboardInterrupt:
            print("\n")
            print("=======================================================")
            print("👋 Coding Assistant interrupted!")
            print("💾 Don't forget to save your work!")
            print("🎉 See you next time!")
            print("=======================================================")
            break
        except Exception as e:
            print(f"❌ An error occurred: {str(e)}")
            print("🔧 Please try again or type 'exit' to quit")
            print()