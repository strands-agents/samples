from typing import Any
from strands.types.tools import ToolResult, ToolUse
import boto3
import uuid

TOOL_SPEC = {
    "name": "create_booking",
    "description": "Create a new booking at restaurant_name",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": """The date of the booking in the format YYYY-MM-DD. 
                    Do NOT accept relative dates like today or tomorrow. 
                    Ask for today's date for relative date."""
                },
                "hour": {
                    "type": "string",
                    "description": "the hour of the booking in the format HH:MM"
                },
                "restaurant_name": {
                    "type": "string",
                    "description": "name of the restaurant handling the reservation"
                },
                "guest_name": {
                    "type": "string",
                    "description": "The name of the customer to have in the reservation"
                },
                "num_guests": {
                    "type": "integer",
                    "description": "The number of guests for the booking"
                }
            },
            "required": ["date", "hour", "restaurant_name", "guest_name", "num_guests"]
        }
    }
}
# Function name must match tool name
def create_booking(tool: ToolUse, **kwargs: Any) -> ToolResult:
    kb_name = 'restaurant-assistant'
    dynamodb = boto3.resource('dynamodb')
    smm_client = boto3.client('ssm')
    table_name = smm_client.get_parameter(
        Name=f'{kb_name}-table-name',
        WithDecryption=False
    )
    table = dynamodb.Table(table_name["Parameter"]["Value"])
    
    tool_use_id = tool["toolUseId"]
    date = tool["input"]["date"]
    hour = tool["input"]["hour"]
    restaurant_name = tool["input"]["restaurant_name"]
    guest_name = tool["input"]["guest_name"]
    num_guests = tool["input"]["num_guests"]
    
    results = f"Creating reservation for {num_guests} people at {restaurant_name}, " \
              f"{date} at {hour} in the name of {guest_name}"
    print(results)
    try:
        booking_id = str(uuid.uuid4())[:8]
        table.put_item(
            Item={
                'booking_id': booking_id,
                'restaurant_name': restaurant_name,
                'date': date,
                'name': guest_name,
                'hour': hour,
                'num_guests': num_guests
            }
        )
        return {
            "toolUseId": tool_use_id,
            "status": "success",
            "content": [{"text": f"Reservation created with booking id: {booking_id}"}]
        } 
    except Exception as e:
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": str(e)}]
        } 
