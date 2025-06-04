import sqlite3
import uuid
from datetime import datetime
from strands import tool

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