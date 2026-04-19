import os
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import current_time
from calendar_tools import create_appointment, get_agenda, list_appointments, update_appointment
from constants import SESSION_ID

# Show rich UI for tools in CLI
os.environ["STRANDS_TOOL_CONSOLE_MODE"] = "enabled"


@tool
def calendar_assistant(query: str) -> str:
    """
    Calendar assistant agent to manage appointments.
    Args:
        query: A request to the calendar assistant

    Returns:
        Output from interaction
    """
    # Call the agent and return its response
    response = agent(query)
    print("\n\n")
    return str(response)


system_prompt = """You are a helpful calendar assistant that specializes in managing my appointments. 
You have access to appointment management tools, and can check the current time to help me organize my schedule effectively. 
Always provide the appointment id so that I can update it if required"""

model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
)

agent = Agent(
    model=model,
    system_prompt=system_prompt,
    tools=[
        current_time,
        create_appointment,
        list_appointments,
        update_appointment,
        get_agenda
    ],
    trace_attributes={"session.id": SESSION_ID},
)


if __name__ == "__main__":
    print("=" * 60)
    print("🗓️  WELCOME TO YOUR PERSONAL CALENDAR ASSISTANT  🗓️")
    print("=" * 60)
    print("✨ I can help you with:")
    print("   📅 Create new appointments")
    print("   📋 List all your appointments") 
    print("   🔄 Update existing appointments")
    print("   📆 Get your daily agenda")
    print("   🕐 Check current time")
    print()
    print("💡 Tips:")
    print("   • Use dates in format: YYYY-MM-DD HH:MM")
    print("   • I'll always provide appointment IDs for updates")
    print("   • Try: 'What's my agenda for today?' or 'Book a meeting'")
    print()
    print("🚪 Type 'exit' to quit anytime")
    print("=" * 60)
    print()

    # Run the agent in a loop for interactive conversation
    while True:
        try:
            user_input = input("👤 You: ").strip()

            if not user_input:
                print("💭 Please enter a message or type 'exit' to quit")
                continue

            if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                print()
                print("=======================================")
                print("👋 Thanks for using Calendar Assistant!")
                print("🎉 Have a great day ahead!")
                print("=======================================")
                break

            print("🤖 CalendarBot: ", end="")
            response = calendar_assistant(user_input)

        except KeyboardInterrupt:
            print()
            print("=======================================")
            print("👋 Calendar Assistant interrupted!")
            print("🎉 See you next time!")
            print("=======================================")
            break
        except Exception as e:
            print(f"❌ An error occurred: {str(e)}")
            print("💡 Please try again or type 'exit' to quit")
            print()