import sqlite3
import os
from strands import tool

@tool
def list_appointments() -> str:
    """
    List all available appointments from the database.
    
    Returns:
        str: the appointments available 
    """
    # Check if database exists
    if not os.path.exists('appointments.db'):
        return "No appointment available"
    
    conn = sqlite3.connect('appointments.db')
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()
    
    # Check if the appointments table exists
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='appointments'")
        if not cursor.fetchone():
            conn.close()
            return "No appointment available"
        
        cursor.execute("SELECT * FROM appointments ORDER BY date")
        rows = cursor.fetchall()
        
        # Convert rows to dictionaries
        appointments = []
        for row in rows:
            appointment = {
                'id': row['id'],
                'date': row['date'],
                'location': row['location'],
                'title': row['title'],
                'description': row['description']
            }
            appointments.append(appointment)
        
        conn.close()
        print(f"Retrieved {len(appointments)} appointments")
        return str(appointments)
    
    except sqlite3.Error:
        conn.close()
        return []


