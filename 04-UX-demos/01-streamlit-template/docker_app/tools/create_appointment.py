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
        str: The ID of the newly created appointment.

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
    return f"Appointment with id {appointment_id} created"
