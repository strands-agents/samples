import sqlite3
import uuid
from datetime import datetime
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import current_time
import list_appointments
import update_appointment


@tool
def create_appointment(date: str, location: str, title: str, description: str) -> str:
    """
    Create a new personal appointment in the database.

    Args:
        date (str): Date and time of the appointment (format: YYYY-MM-DD HH:MM).
        location (str): Location of the appointment.
        title (str): Title of the appointment.
        description (str): Description of the appointment.

    Returns:
        str: Formatted confirmation of the newly created appointment.

    Raises:
        ValueError: If the date format is invalid.
    """
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d %H:%M")
    except ValueError:
        raise ValueError("Date must be in format 'YYYY-MM-DD HH:MM'")

    # Generate a unique ID
    appointment_id = str(uuid.uuid4())

    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()

    # Create the appointments table if it doesn't exist
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS appointments (
        id TEXT PRIMARY KEY,
        date TEXT,
        location TEXT,
        title TEXT,
        description TEXT
    )
    """
    )

    cursor.execute(
        "INSERT INTO appointments (id, date, location, title, description) VALUES (?, ?, ?, ?, ?)",
        (appointment_id, date, location, title, description),
    )

    conn.commit()
    conn.close()

    # Format the confirmation with same style as get_agenda
    time_part = date.split(" ")[1] if " " in date else "No time specified"
    date_part = date.split(" ")[0] if " " in date else date
    confirmation = [
        "✅ Appointment Created Successfully!",
        "=====================================",
        f"📅 Date: {date_part}",
        f"🕐 Time: {time_part}",
        f"📍 Location: {location}",
        f"📝 Title: {title}",
        f"📄 Description: {description}",
        f"🆔 ID: {appointment_id}",
        "",
        "Your appointment has been saved to your calendar!"
    ]
    return "\n".join(confirmation)


@tool
def get_agenda(date: str) -> str:
    """
    Retrieve the agenda for a specific day, showing all appointments scheduled for that date.

    Args:
        date (str): Date to get agenda for (format: YYYY-MM-DD).

    Returns:
        str: Formatted agenda for the specified date with all appointments.

    Raises:
        ValueError: If the date format is invalid.
    """
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Date must be in format 'YYYY-MM-DD'")

    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()

    # Create the appointments table if it doesn't exist
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS appointments (
        id TEXT PRIMARY KEY,
        date TEXT,
        location TEXT,
        title TEXT,
        description TEXT
    )
    """
    )

    # Query appointments for the specific date (using LIKE to match the date part)
    cursor.execute(
        "SELECT id, date, location, title, description FROM appointments WHERE date LIKE ? ORDER BY date",
        (f"{date}%",)
    )

    appointments = cursor.fetchall()
    conn.close()

    if not appointments:
        return f"No appointments scheduled for {date}"

    # Format the agenda
    agenda_lines = [f"📅 Agenda for {date}:", "=" * 30]

    for appointment in appointments:
        appointment_id, appointment_date, location, title, description = appointment
        # Extract time from the datetime string
        time_part = appointment_date.split(" ")[1] if " " in appointment_date else "No time specified"

        agenda_lines.append(f"🕐 {time_part} - {title}")
        agenda_lines.append(f"   📍 Location: {location}")
        agenda_lines.append(f"   📝 Description: {description}")
        agenda_lines.append(f"   🆔 ID: {appointment_id}")
        agenda_lines.append("")  # Empty line for spacing

    return "\n".join(agenda_lines)


@tool
def calendar_assistant(query: str) -> str:
    """
    Calendar assistant agent to manage appointments.
    Args:
        query: A request to the calendar assistant

    Returns:
        Output from interaction
    """
    system_prompt = """You are a helpful calendar assistant that specializes in managing my appointments. 
    You have access to appointment management tools, and can check the current time to help me organize my schedule effectively. 
    Always provide the appointment id so that I can update it if required"""

    model = BedrockModel(
        model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
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
    )
    # Call the agent and return its response
    response = agent(query)
    return str(response)


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
            print(response)
            print()

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