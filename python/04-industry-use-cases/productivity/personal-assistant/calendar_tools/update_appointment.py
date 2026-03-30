import sqlite3
from datetime import datetime
import os
from strands.types.tools import ToolResult, ToolUse
from typing import Any

TOOL_SPEC = {
    "name": "update_appointment",
    "description": "Update an appointment based on the appointment ID.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "appointment_id": {
                    "type": "string",
                    "description": "The appointment id."
                },
                "date": {
                    "type": "string",
                    "description": "Date and time of the appointment (format: YYYY-MM-DD HH:MM)."
                },
                "location": {
                    "type": "string",
                    "description": "Location of the appointment."
                },
                "title": {
                    "type": "string",
                    "description": "Title of the appointment."
                },
                "description": {
                    "type": "string",
                    "description": "Description of the appointment."
                }
            },
            "required": ["appointment_id"]
        }
    }
}


# Function name must match tool name
def update_appointment(tool: ToolUse, **kwargs: Any) -> ToolResult:
    tool_use_id = tool["toolUseId"]
    appointment_id = tool["input"]["appointment_id"]
    
    date = tool["input"].get("date")
    location = tool["input"].get("location")
    title = tool["input"].get("title")
    description = tool["input"].get("description")

    # Check if database exists
    if not os.path.exists('appointments.db'): 
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": "❌ Error: No appointments database found."}]
        }
    # Check if appointment exists
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()

    # Check if the appointments table exists
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='appointments'")
        if not cursor.fetchone():
            conn.close()
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": "❌ Error: Appointments table does not exist."}]
            }

        cursor.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
        appointment = cursor.fetchone()

        if not appointment:
            conn.close()
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": f"❌ Error: Appointment with ID {appointment_id} does not exist."}]
            }

        # Store original values for comparison
        original_date, original_location, original_title, original_description = appointment[1:5]

        # Validate date format if provided
        if date:
            try:
                datetime.strptime(date, '%Y-%m-%d %H:%M')
            except ValueError:
                conn.close()
                return {
                    "toolUseId": tool_use_id,
                    "status": "error",
                    "content": [{"text": "❌ Error: Date must be in format 'YYYY-MM-DD HH:MM'"}]
                }

        # Build update query
        update_fields = []
        params = []
        changes = []

        if date and date != original_date:
            update_fields.append("date = ?")
            params.append(date)
            old_date_part = original_date.split(" ")[0] if " " in original_date else original_date
            old_time_part = original_date.split(" ")[1] if " " in original_date else "No time"
            new_date_part = date.split(" ")[0] if " " in date else date
            new_time_part = date.split(" ")[1] if " " in date else "No time"
            changes.append(f"📅 Date: {old_date_part} {old_time_part} → {new_date_part} {new_time_part}")

        if location and location != original_location:
            update_fields.append("location = ?")
            params.append(location)
            changes.append(f"📍 Location: {original_location} → {location}")

        if title and title != original_title:
            update_fields.append("title = ?")
            params.append(title)
            changes.append(f"📝 Title: {original_title} → {title}")

        if description and description != original_description:
            update_fields.append("description = ?")
            params.append(description)
            changes.append(f"📄 Description: {original_description} → {description}")

        # If no fields to update
        if not update_fields:
            conn.close()
            return {
                "toolUseId": tool_use_id,
                "status": "success",
                "content": [{"text": "ℹ️ No changes needed - your appointment is already up to date! ✨"}]
            }

        # Complete the query
        query = f"UPDATE appointments SET {', '.join(update_fields)} WHERE id = ?"
        params.append(appointment_id)

        cursor.execute(query, params)
        conn.commit()
        conn.close()

        # Format the success message
        update_confirmation = [
            "✅ Appointment Updated Successfully!",
            "=======================================",
            f"🆔 Appointment ID: {appointment_id}",
            "",
            "📝 Changes Made:"
        ]

        for change in changes:
            update_confirmation.append(f"   {change}")

        update_confirmation.extend([
            "",
            "Your appointment has been updated! 🎉"
        ])

        return {
            "toolUseId": tool_use_id,
            "status": "success",
            "content": [{"text": "\n".join(update_confirmation)}]
        }
    except sqlite3.Error as e:
        conn.close()
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": f"❌ Database error: {str(e)}"}]
        }