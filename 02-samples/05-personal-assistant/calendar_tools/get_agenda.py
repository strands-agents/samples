import sqlite3
from datetime import datetime
from strands import tool

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