#!/usr/bin/env python3
"""
Boston Dynamics Spot Robot Control Agent with Strands 

Supports multiple LLM providers via Strands Agents framework.
Configure your preferred model via the MODEL environment variable.
"""

import os
import asyncio
import time

from dotenv import load_dotenv
from strands import Agent
from strands_tools import think

# Import spot tools directly
from spot_mcp_server import (
    connect_to_robot,
    robot_force_take_lease,
    robot_stand,
    robot_sit,
    robot_stop,
    robot_get_status,
    robot_toggle_power,
    robot_self_right,
    robot_move_forward,
    robot_move_backward,
    robot_strafe_left,
    robot_strafe_right,
    robot_turn_left,
    robot_turn_right,
    robot_battery_change_pose,
    robot_take_image,
    robot_dock,
    robot_undock,
    robot_get_dock_status,
)

# Load environment variables
load_dotenv()

# Get model from environment (supports any Strands-compatible model)
MODEL = os.getenv("MODEL", "global.anthropic.claude-sonnet-4-5-20250929-v1:0")


AGENT_PROMPT = """
You are a Boston Dynamics Spot Robot Control Agent, an expert assistant for operating and managing Spot quadruped robots through remote commands.

## Core Identity & Purpose
You are a specialized robotic systems operator with deep knowledge of:
- Boston Dynamics Spot robot capabilities and limitations
- Safe robotic operation procedures and best practices
- Remote robot control through API commands
- Situational awareness and safety protocols
- Troubleshooting common robotic system issues

## Connection Management
When the user asks to connect to the robot:
- Check if they provide specific connection details (hostname, username, password)
- If they don't provide details, call connect_to_robot() without arguments - it will use environment variables (ROBOT_HOSTNAME, ROBOT_USERNAME, ROBOT_PASSWORD) from the .env file
- Example: If user says "connect to robot", use connect_to_robot() with no arguments
- Always confirm successful connection before proceeding with other commands

## Primary Responsibilities

### Robot Operation & Control
- Execute movement commands (forward, backward, strafe, turn) with appropriate parameters
- Manage robot posture (stand, sit, self-right, battery change pose)
- Control docking and undocking operations with charging station
- Monitor and control power states and system status
- Handle emergency situations with immediate stop/estop commands
- Coordinate complex movement sequences and navigation tasks

### Safety & Risk Management
- Always prioritize safety in all robot operations
- Verify robot status before executing potentially dangerous commands
- Provide clear warnings about space requirements and environmental hazards
- Implement proper shutdown procedures when issues arise
- Monitor battery levels and power states continuously

### System Administration
- Manage robot lease acquisition and release
- Handle authentication and connection establishment
- Monitor system health through status checks
- Coordinate docking status and charging state monitoring
- Coordinate image capture and environmental sensing
- Troubleshoot connectivity and communication issues

### User Guidance & Education
- Explain robot capabilities and limitations clearly
- Provide step-by-step guidance for complex operations
- Educate users on safe operating procedures
- Recommend best practices for different scenarios
- Help users understand robot feedback and status information

## Operational Protocol

### Before Any Robot Commands:
1. **Connection Check**: Ensure robot connection is established via connect_to_robot()
2. **Status Verification**: Check robot status including power, lease, and estop states
3. **Safety Assessment**: Verify adequate space and safe operating conditions
4. **User Intent**: Confirm understanding of user's goals and constraints

### During Operations:
1. **Progressive Commands**: Start with simple, safe commands before complex maneuvers
2. **Status Monitoring**: Regularly check robot status during extended operations
3. **Error Handling**: Immediately address any error conditions or unexpected behavior
4. **User Communication**: Keep user informed of robot actions and status changes

### Emergency Procedures:
1. **Immediate Stop**: Use robot_stop() for immediate motion cessation
2. **Emergency Stop**: Use robot_toggle_estop() for complete system lockdown
3. **Safe Shutdown**: Execute robot_sit() followed by power off for safe shutdown
4. **Status Assessment**: Check robot_get_status() to understand system state

## Communication Style
- **Clear & Precise**: Use specific technical language when appropriate
- **Safety-Focused**: Always mention safety considerations and precautions
- **Step-by-Step**: Break complex operations into clear, sequential steps
- **Proactive**: Anticipate potential issues and provide preventive guidance
- **Responsive**: Acknowledge user concerns and provide immediate assistance

## Key Safety Principles
- Never assume robot environment is clear - always verify
- Maintain situational awareness of robot's physical state
- Prioritize human safety over mission completion
- Use minimum necessary force/speed for tasks
- Always have emergency stop procedures ready
- Respect robot's physical and operational limitations

## Interaction Guidelines
- Begin each session by establishing robot connection and status
- Confirm user's experience level with robot operations
- Provide appropriate level of detail based on user expertise
- Offer to demonstrate basic operations before complex tasks
- Always end sessions with proper robot shutdown procedures

Remember: You are responsible for safe, effective robot operation. When in doubt, choose the more conservative, safer approach. The robot is a powerful tool that requires respect and careful handling.
"""


def print_welcome():
    """Print welcome message and basic instructions."""
    print("🤖 Boston Dynamics Spot Robot Control Agent")
    print("=" * 60)
    print("Welcome! I'm your Spot robot control assistant.")
    print("\nI can help you:")
    print("• Connect to and control your Spot robot")
    print("• Execute movement commands safely")
    print("• Monitor robot status and health")
    print("• Capture images from robot cameras")
    print("• Manage power, lease, and safety systems")
    print("\n⚠️  SAFETY REMINDER: Always ensure adequate space around the robot")
    print("   and maintain visual contact during operations.")
    print("\nType 'help' for command examples or 'exit' to quit.")
    print("=" * 60)


def print_help():
    """Print helpful command examples."""
    print("\n📋 Common Commands & Examples:")
    print("-" * 40)
    print("🔌 Connection:")
    print("  • 'Connect to robot at 192.168.1.100'")
    print("  • 'Check robot status'")
    print("\n🚶 Basic Movement:")
    print("  • 'Stand up'")
    print("  • 'Move forward for 2 seconds'")
    print("  • 'Turn left 90 degrees'")
    print("  • 'Sit down'")
    print("\n🔌 Docking & Charging:")
    print("  • 'Dock with charging station'")
    print("  • 'Undock from charger'")
    print("  • 'Check dock status'")
    print("\n📸 Sensing:")
    print("  • 'Take a picture'")
    print("  • 'Show me what the robot sees'")
    print("\n⚡ System Control:")
    print("  • 'Check battery level'")
    print("  • 'Emergency stop'")
    print("  • 'Power off safely'")
    print("\n🔧 Advanced:")
    print("  • 'Self-right the robot'")
    print("  • 'Position for battery change'")
    print("  • 'Execute patrol sequence'")
    print("-" * 40)


async def process_streaming_command(agent, user_input):
    """
    Process command
    """
    # Track timing
    total_start = time.time()
    model_start = None
    first_token_time = None

    # Show immediate feedback
    print("\n🔄 Processing command...")
    if any(
        word in user_input.lower()
        for word in ["connect", "stand", "sit", "move", "status"]
    ):
        print("⏳ Executing robot command...")

    try:
        model_start = time.time()

        async for event in agent.stream_async(user_input):
            # Track event loop lifecycle
            if event.get("init_event_loop", False):
                print("\n🔄 Event loop initialized")
            elif event.get("start_event_loop", False):
                print("▶️ Event loop cycle starting")
            elif "message" in event:
                print(f"📬 New message created: {event['message']['role']}")
            elif event.get("complete", False):
                print("✅ Cycle completed")
            elif event.get("force_stop", False):
                print(
                    f"🛑 Event loop force-stopped: {event.get('force_stop_reason', 'unknown reason')}"
                )

            # Track tool usage 
            if "current_tool_use" in event and event["current_tool_use"].get("name"):
                tool_name = event["current_tool_use"]["name"]
                print(f"🔧 Using tool: {tool_name}")

            # Stream text chunks
            if "data" in event:
                if first_token_time is None:
                    first_token_time = time.time() - model_start
                    print("\n📟 Streaming response:")
                # Print the actual text data (not truncated like docs example)
                print(event["data"], end="", flush=True)

        # Calculate timing
        total_time = time.time() - total_start
        model_time = time.time() - model_start if model_start else 0

        print(f"\n\n📊 Timing Breakdown:")
        if first_token_time:
            print(f"   • Time to First Token: {first_token_time:.2f}s")
        print(f"   • Model Total Time: {model_time:.2f}s")
        print(f"   • Total Execution Time: {total_time:.2f}s")

    except Exception as e:
        print(f"\n\n❌ Streaming error: {str(e)}")
        raise


async def main():
    """Main async function for the agent."""
    print_welcome()

    # Collect all robot control tools
    tool_list = [
        connect_to_robot,
        robot_force_take_lease,
        robot_stand,
        robot_sit,
        robot_stop,
        robot_get_status,
        robot_toggle_power,
        robot_self_right,
        robot_move_forward,
        robot_move_backward,
        robot_strafe_left,
        robot_strafe_right,
        robot_turn_left,
        robot_turn_right,
        robot_battery_change_pose,
        robot_take_image,
        robot_dock,
        robot_undock,
        robot_get_dock_status,
        think,
    ]

    print(f"\n✅ Loaded {len(tool_list) - 1} robot tools")
    print(f"🤖 Using model: {MODEL}")

    try:
        # Initialize agent with configured model, tools and system prompt
        agent = Agent(
            model=MODEL,
            tools=tool_list,
            system_prompt=AGENT_PROMPT,
            callback_handler=None,  
        )

        # Interactive loop
        while True:
            try:
                user_input = input("\n🤖 > ").strip()

                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("\n👋 Shutting down robot control agent...")
                    print(
                        "Remember to safely power down your robot if still connected."
                    )
                    break

                if user_input.lower() in ["help", "?"]:
                    print_help()
                    continue

                if not user_input:
                    continue

                # Process command with streaming
                await process_streaming_command(agent, user_input)

                # Add a separator for readability
                print("-" * 50)

            except KeyboardInterrupt:
                print("\n\n⚠️  Interrupted! Attempting safe shutdown...")
                try:
                    # Attempt to safely stop robot if connected
                    print("Sending emergency stop command...")
                    await process_streaming_command(
                        agent, "Emergency stop the robot and sit down safely"
                    )
                except:
                    pass
                print("Exiting robot control agent.")
                break

            except Exception as e:
                print(f"\n❌ Error occurred: {str(e)}")
                print(
                    "The robot may still be operational. Check robot status before continuing."
                )
                print("Type 'help' for command examples or 'exit' to quit safely.")

    except Exception as e:
        print(f"\n❌ Failed to initialize agent: {str(e)}")
        print("\nTroubleshooting:")
        print(
            "1. Check that Boston Dynamics SDK is installed: pip install bosdyn-client"
        )
        print("2. Verify your MODEL environment variable is set correctly")
        print("3. Ensure your LLM provider credentials are configured")
        print("4. For AWS Bedrock: configure AWS_REGION and AWS credentials")
        print("5. For other providers: see Strands documentation")


if __name__ == "__main__":
    asyncio.run(main())
