#!/usr/bin/env python3
"""
Measure the token overhead of loading Boston Dynamics Spot tools.

This script helps understand how many input tokens are consumed
just by tool specifications being loaded into the agent's context.
"""

import os
import asyncio
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

# Get model from environment
MODEL = os.getenv("MODEL", "global.anthropic.claude-sonnet-4-5-20250929-v1:0")

# Minimal agent prompt for baseline measurement
MINIMAL_PROMPT = "You are a robot control assistant."

# Full agent prompt from main agent
FULL_AGENT_PROMPT = """
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


async def measure_baseline_tokens(tools, system_prompt, test_message="Hello"):
    """Measure token usage for a simple message with given tools and prompt."""
    
    input_tokens = 0
    output_tokens = 0
    
    try:
        # Create agent
        agent = Agent(
            model=MODEL,
            tools=tools,
            system_prompt=system_prompt,
            callback_handler=None,
        )
        
        # Process a simple message
        async for event in agent.stream_async(test_message):
            if "usage" in event:
                usage = event["usage"]
                if "input_tokens" in usage:
                    input_tokens += usage["input_tokens"]
                if "output_tokens" in usage:
                    output_tokens += usage["output_tokens"]
        
        return input_tokens, output_tokens
        
    except Exception as e:
        print(f"Error measuring tokens: {e}")
        return 0, 0


async def main():
    """Measure token overhead from tools and system prompt."""
    
    print("🪙 Boston Dynamics Spot Tools - Token Overhead Analysis")
    print("=" * 60)
    print(f"Model: {MODEL}")
    print("=" * 60)
    
    # Collect all robot control tools
    all_tools = [
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
    
    print(f"\nTotal tools loaded: {len(all_tools)}")
    print(f"Robot control tools: {len(all_tools) - 1}")
    print(f"Additional tools: 1 (think)")
    
    # Test configurations
    test_configs = [
        ("Baseline (no tools, minimal prompt)", [], MINIMAL_PROMPT),
        ("With tools only (minimal prompt)", all_tools, MINIMAL_PROMPT),
        ("With full prompt only (no tools)", [], FULL_AGENT_PROMPT),
        ("Full configuration (all tools + full prompt)", all_tools, FULL_AGENT_PROMPT),
    ]
    
    results = []
    
    for config_name, tools, prompt in test_configs:
        print(f"\n📊 Testing: {config_name}")
        print("   Measuring token usage...")
        
        input_tokens, output_tokens = await measure_baseline_tokens(
            tools, prompt, "Hello"
        )
        
        results.append({
            "config": config_name,
            "input": input_tokens,
            "output": output_tokens,
            "total": input_tokens + output_tokens
        })
        
        print(f"   ✓ Input tokens: {input_tokens:,}")
        print(f"   ✓ Output tokens: {output_tokens:,}")
        print(f"   ✓ Total tokens: {input_tokens + output_tokens:,}")
    
    # Calculate overhead
    print("\n" + "=" * 60)
    print("📈 TOKEN OVERHEAD ANALYSIS")
    print("=" * 60)
    
    baseline = results[0]["input"]
    tools_only = results[1]["input"] - baseline
    prompt_only = results[2]["input"] - baseline
    full_overhead = results[3]["input"] - baseline
    
    print(f"\n🎯 Baseline (minimal agent): {baseline:,} tokens")
    print(f"\n🔧 Tools overhead: {tools_only:,} tokens")
    print(f"   • Per tool average: {tools_only // len(all_tools):,} tokens")
    print(f"   • This is the cost of loading {len(all_tools)} tool specifications")
    
    print(f"\n📝 System prompt overhead: {prompt_only:,} tokens")
    print(f"   • Full safety/operational prompt adds this many tokens")
    
    print(f"\n💰 Total overhead: {full_overhead:,} tokens")
    print(f"   • This is added to EVERY request when using the full agent")
    if baseline > 0:
        print(f"   • Percentage of baseline: {(full_overhead / baseline * 100):.1f}%")
    else:
        print(f"   • Percentage of baseline: N/A (baseline is 0)")
    
    # Recommendations
    print("\n" + "=" * 60)
    print("💡 RECOMMENDATIONS")
    print("=" * 60)
    print("\n1. Token Efficiency:")
    print(f"   • Each tool adds ~{tools_only // len(all_tools):,} tokens on average")
    print("   • Consider loading only necessary tools for specific tasks")
    
    print("\n2. Cost Optimization:")
    print("   • For simple queries, the overhead might exceed the actual response")
    print("   • Consider creating task-specific agents with fewer tools")
    
    print("\n3. Tool Selection:")
    print("   • Prioritize frequently used tools")
    print("   • Group tools by function and load as needed")
    
    # Cost estimation (example rates)
    input_rate = 0.001  # $0.001 per 1K tokens (example)
    output_rate = 0.002  # $0.002 per 1K tokens (example)
    
    print(f"\n💵 Cost Impact (at ${input_rate}/1K input, ${output_rate}/1K output):")
    overhead_cost = (full_overhead * input_rate) / 1000
    print(f"   • Overhead cost per request: ${overhead_cost:.4f}")
    print(f"   • Cost for 1,000 requests: ${overhead_cost * 1000:.2f}")
    print(f"   • Cost for 10,000 requests: ${overhead_cost * 10000:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
