import os
import json
from datetime import datetime, timedelta
from strands import Agent, tool
from strands.models import BedrockModel
from aws_config import get_bedrock_session

# Mock database for time off information
employee_time_off = {
    "total_days": 25,
    "used_days": 10,
    "pending_requests": []
}

@tool
def get_time_off() -> str:
    """Get the current time off balance for the employee.
    
    Returns:
        A JSON string containing the employee's time off information.
    """
    remaining_days = employee_time_off["total_days"] - employee_time_off["used_days"]
    
    response = {
        "total_days": employee_time_off["total_days"],
        "used_days": employee_time_off["used_days"],
        "remaining_days": remaining_days,
        "pending_requests": employee_time_off["pending_requests"]
    }
    
    return json.dumps(response)

@tool
def request_time_off(start_date: str, number_of_days: int) -> str:
    """Submit a time off request for the employee.
    
    Args:
        start_date: The date that time off starts (format: YYYY-MM-DD)
        number_of_days: The number of days user wants to request off
    
    Returns:
        A JSON string containing the result of the time off request or a confirmation request.
    """
    try:
        # Parse the start date
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        
        # Check if the date is in the past
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if start_date_obj < today:
            response = {
                "success": False,
                "message": "Invalid date. Time off requests cannot be made for dates in the past."
            }
            return json.dumps(response)
        
        # Calculate the end date
        end_date_obj = start_date_obj + timedelta(days=number_of_days - 1)
        end_date = end_date_obj.strftime("%Y-%m-%d")
        
        # Return a confirmation request
        response = {
            "success": True,
            "requires_confirmation": True,
            "message": f"Please confirm your time off request for {start_date} to {end_date} ({number_of_days} days)",
            "request_details": {
                "start_date": start_date,
                "end_date": end_date,
                "number_of_days": number_of_days
            }
        }
        
        return json.dumps(response)
    except ValueError:
        response = {
            "success": False,
            "message": "Invalid date format. Please use YYYY-MM-DD format."
        }
        return json.dumps(response)
    except Exception as e:
        response = {
            "success": False,
            "message": f"Error processing request: {str(e)}"
        }
        return json.dumps(response)

@tool
def confirm_time_off_request(start_date: str, end_date: str, number_of_days: int, confirm: bool) -> str:
    """Confirm or cancel a time off request.
    
    Args:
        start_date: The date that time off starts (format: YYYY-MM-DD)
        end_date: The date that time off ends (format: YYYY-MM-DD)
        number_of_days: The number of days requested off
        confirm: Boolean indicating whether to confirm (True) or cancel (False) the request
    
    Returns:
        A JSON string containing the result of the confirmation.
    """
    try:
        if not confirm:
            response = {
                "success": True,
                "message": "Time off request cancelled."
            }
            return json.dumps(response)
        
        # Create a new request
        request = {
            "start_date": start_date,
            "end_date": end_date,
            "number_of_days": number_of_days,
            "status": "pending"
        }
        
        # Add the request to the pending requests
        employee_time_off["pending_requests"].append(request)
        
        response = {
            "success": True,
            "message": f"Time off request confirmed and submitted for {start_date} to {end_date} ({number_of_days} days)",
            "request": request
        }
        
        return json.dumps(response)
    except Exception as e:
        response = {
            "success": False,
            "message": f"Error confirming request: {str(e)}"
        }
        return json.dumps(response)


def event_loop_tracker(**kwargs):
    # Track event loop lifecycle
    if kwargs.get("init_event_loop", False):
        print("🔄 Event loop initialized")
    elif kwargs.get("start_event_loop", False):
        print("▶️ Event loop cycle starting")
    elif kwargs.get("start", False):
        print("📝 New cycle started")
    elif "message" in kwargs:
        print(f"📬 New message created: {kwargs['message']['role']}")
    elif kwargs.get("complete", False):
        print("✅ Cycle completed")
    elif kwargs.get("force_stop", False):
        print(f"🛑 Event loop force-stopped: {kwargs.get('force_stop_reason', 'unknown reason')}")

    # Track tool usage
    if "current_tool_use" in kwargs and kwargs["current_tool_use"].get("name"):
        tool_name = kwargs["current_tool_use"]["name"]
        print(f"🔧 Using tool: {tool_name}")


def create_hr_assistant():
    """Create and configure the HR assistant agent."""
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), "BedrockAgentStack", "config.json")
    with open(config_path, "r") as config_file:
        config = json.load(config_file)
    
    # Get the Bedrock session
    bedrock_session = get_bedrock_session()
    
    # Create the Bedrock model with the client
    bedrock_model = BedrockModel(
        model_id=config["agentModelId"],
        # client=bedrock_client
        boto_session=bedrock_session
    )
    
    # Create the agent with system prompt, model, and tools
    agent = Agent(
        system_prompt=config["agentInstruction"],
        model=bedrock_model,
        tools=[get_time_off, request_time_off, confirm_time_off_request],
        callback_handler=event_loop_tracker
    )
    
    return agent

def main():
    """Main function to run the HR assistant agent."""
    agent = create_hr_assistant()
    
    print("HR Assistant Agent is ready!")
    print("You can now interact with the agent.")
    print("Type 'exit' to quit.")
    
    # Start conversation
    while True:
        user_input = input("\nYou: ")
        
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        
        # Process the user input and get a response
        response = agent(user_input)
        
        # Print the response
        print(f"\nHR Assistant: {response}")

if __name__ == "__main__":
    main()
