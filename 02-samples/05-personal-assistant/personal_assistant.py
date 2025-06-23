import os
from strands import Agent
from strands.models import BedrockModel
from code_assistant import code_assistant
from calendar_assistant import calendar_assistant
from search_assistant import search_assistant
from constants import SESSION_ID

# Show rich UI for tools in CLI
os.environ["STRANDS_TOOL_CONSOLE_MODE"] = "enabled"

model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
)

personal_assistant_agent = Agent(
    model=model,
    system_prompt="You are a personal assistant. Use the agents and tools at your disposal to assist the user.",
    tools=[code_assistant, calendar_assistant, search_assistant],
    trace_attributes={"session.id": SESSION_ID},
)


if __name__ == "__main__":
    print("=============================================================================")
    print("🤖  WELCOME TO YOUR  PERSONAL ASSISTANT  🤖")
    print("=============================================================================")
    print("✨ I'm your intelligent coordinator with access to:")
    print("   📅 Calendar Assistant - Schedule and manage appointments")
    print("   💻 Coding Assistant - Write, debug, and manage code")
    print("   🔍 Search Assistant - Research and find information")
    print()
    print("🎯 I can handle complex requests across multiple domains:")
    print("   • 'Schedule a meeting and research the attendees'")
    print("   • 'Code a script and schedule time to work on it'")
    print("   • 'What's my agenda and help me prepare presentations'")
    print()
    print("💡 Just tell me what you need - I'll coordinate everything!")
    print("🚪 Type 'exit' to quit anytime")
    print("=============================================================================")
    print()

    # Initialize the personal assistant
    try:
        print("🔄 Initializing Personal Assistant...")
        print("✅ Personal Assistant ready!")
        print("🤖 All specialized agents are available!")
        print()
    except Exception as e:
        print(f"❌ Error initializing Personal Assistant: {str(e)}")

    # Run the agent in a loop for interactive conversation
    while True:
        try:
            user_input = input("👤 You: ").strip()
            if not user_input:
                print("💭 Please tell me how I can help you, or type 'exit' to quit")
                continue
            if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                print()
                print("=========================================================")
                print("👋 Thank you for using Personal Assistant!")
                print("🎉 Have a productive day ahead!")
                print("🤖 Come back anytime you need help!")
                print("=========================================================")
                break

            print("🤖 PersonalBot: ", end="")
            response = personal_assistant_agent(user_input)
            print("\n")

        except KeyboardInterrupt:
            print("\n")
            print("=========================================================")
            print("👋 Personal Assistant interrupted!")
            print("🤖 See you next time!")
            print("=========================================================")
            break
        except Exception as e:
            print(f"❌ An error occurred: {str(e)}")
            print("🔧 Please try again or type 'exit' to quit")
            print()


