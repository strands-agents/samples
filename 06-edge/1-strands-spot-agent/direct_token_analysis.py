#!/usr/bin/env python3
"""
Direct analysis of tool specifications to estimate token overhead.

This script inspects the actual tool objects and their specifications
to provide a realistic estimate of token usage.
"""

import os
import json
import inspect
from typing import Any, Dict, List
from dotenv import load_dotenv

# Import all the spot tools
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
# Try to import think - it might be a module with a function inside
try:
    from strands_tools import think
    # If think is a module, try to get the main function
    if hasattr(think, 'think'):
        think = think.think
    elif hasattr(think, '__call__'):
        # It's already callable
        pass
    else:
        # Skip think if it's not callable
        think = None
except ImportError:
    think = None

# Load environment variables
load_dotenv()

# Token estimation based on OpenAI tokenizer averages
# Rough approximation: ~1 token per 4 characters
CHARS_PER_TOKEN = 4

def estimate_tokens(text: str) -> int:
    """Estimate token count for a given text."""
    if not text:
        return 0
    # More accurate estimation considering punctuation and structure
    # JSON structures, function names, etc. tend to tokenize differently
    return len(text) // CHARS_PER_TOKEN + 5  # Add small overhead

def get_tool_spec(tool: Any) -> Dict[str, Any]:
    """Extract the tool specification as it would be sent to the LLM."""
    spec = {
        "name": tool.__name__,
        "description": inspect.getdoc(tool) or "No description available",
        "parameters": {}
    }
    
    # Get function signature
    sig = inspect.signature(tool)
    
    # Extract parameters
    for param_name, param in sig.parameters.items():
        param_info = {
            "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
            "description": f"Parameter {param_name}",
            "required": param.default == inspect.Parameter.empty
        }
        spec["parameters"][param_name] = param_info
    
    return spec

def analyze_tool_tokens(tool: Any) -> Dict[str, Any]:
    """Analyze token usage for a single tool."""
    spec = get_tool_spec(tool)
    
    # Convert to JSON to see actual serialized size
    json_spec = json.dumps(spec, indent=2)
    
    # Calculate tokens for each component
    name_tokens = estimate_tokens(spec["name"])
    desc_tokens = estimate_tokens(spec["description"])
    params_tokens = estimate_tokens(json.dumps(spec["parameters"]))
    
    # Total includes JSON structure overhead
    total_tokens = estimate_tokens(json_spec)
    
    return {
        "name": spec["name"],
        "spec": spec,
        "json_length": len(json_spec),
        "estimated_tokens": total_tokens,
        "breakdown": {
            "name": name_tokens,
            "description": desc_tokens,
            "parameters": params_tokens,
            "json_overhead": total_tokens - (name_tokens + desc_tokens + params_tokens)
        }
    }

def main():
    """Analyze all tools for token overhead."""
    print("🔍 Boston Dynamics Spot Tools - Direct Token Analysis")
    print("=" * 60)
    print("This analysis inspects actual tool specifications")
    print("to estimate token overhead in the agent context.")
    print("=" * 60)
    
    # All tools
    robot_tools = [
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
    ]
    
    additional_tools = []
    if think is not None:
        additional_tools.append(think)
    all_tools = robot_tools + additional_tools
    
    print(f"\n📊 Analyzing {len(all_tools)} tools:")
    print(f"   • Robot control tools: {len(robot_tools)}")
    print(f"   • Additional tools: {len(additional_tools)}")
    
    # Analyze each tool
    analyses = []
    total_tokens = 0
    total_json_size = 0
    
    print("\n🔧 Detailed Tool Analysis:")
    print("-" * 60)
    
    for i, tool in enumerate(all_tools, 1):
        analysis = analyze_tool_tokens(tool)
        analyses.append(analysis)
        total_tokens += analysis["estimated_tokens"]
        total_json_size += analysis["json_length"]
        
        print(f"\n{i}. {analysis['name']}:")
        print(f"   • JSON size: {analysis['json_length']:,} characters")
        print(f"   • Estimated tokens: {analysis['estimated_tokens']:,}")
        print(f"   • Breakdown:")
        print(f"     - Name: {analysis['breakdown']['name']} tokens")
        print(f"     - Description: {analysis['breakdown']['description']} tokens")
        print(f"     - Parameters: {analysis['breakdown']['parameters']} tokens")
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 SUMMARY - TOOL SPECIFICATION OVERHEAD")
    print("=" * 60)
    
    avg_tokens = total_tokens // len(all_tools)
    avg_json = total_json_size // len(all_tools)
    
    print(f"\n🎯 Total Tool Specifications:")
    print(f"   • Combined JSON size: {total_json_size:,} characters")
    print(f"   • Estimated total tokens: {total_tokens:,}")
    print(f"   • Average per tool: {avg_tokens:,} tokens ({avg_json:,} chars)")
    
    # System prompt overhead
    system_prompt_size = 5876  # Approximate character count of full prompt
    system_prompt_tokens = estimate_tokens("x" * system_prompt_size)
    
    print(f"\n📝 System Prompt Overhead:")
    print(f"   • Full safety prompt: ~{system_prompt_tokens:,} tokens")
    
    print(f"\n💰 TOTAL OVERHEAD PER REQUEST:")
    total_overhead = total_tokens + system_prompt_tokens
    print(f"   • Tools: {total_tokens:,} tokens")
    print(f"   • System prompt: {system_prompt_tokens:,} tokens")
    print(f"   • TOTAL: {total_overhead:,} tokens")
    
    # Cost analysis with real Claude Sonnet pricing
    input_rate = 3.00  # $3 per 1M input tokens
    
    print(f"\n💵 COST IMPACT (Claude Sonnet at ${input_rate:.2f}/1M input tokens):")
    cost_per_request = (total_overhead * input_rate) / 1_000_000
    print(f"   • Overhead cost per request: ${cost_per_request:.4f}")
    print(f"   • Cost for 1,000 requests: ${cost_per_request * 1000:.2f}")
    print(f"   • Cost for 100,000 requests: ${cost_per_request * 100000:.2f}")
    print(f"   • Annual cost (1M requests): ${cost_per_request * 1_000_000:.2f}")
    
    # Find most expensive tools
    sorted_tools = sorted(analyses, key=lambda x: x['estimated_tokens'], reverse=True)
    
    print(f"\n🏆 Top 5 Most Token-Heavy Tools:")
    for i, tool in enumerate(sorted_tools[:5], 1):
        print(f"   {i}. {tool['name']}: {tool['estimated_tokens']:,} tokens")
    
    print("\n💡 OPTIMIZATION STRATEGIES:")
    print("-" * 60)
    print("1. **Tool Grouping**: Create task-specific agents")
    print("   • Movement agent: 8 movement tools only")
    print("   • Status agent: 3-4 status/monitoring tools")
    print("   • Maintenance agent: docking/power tools")
    
    print("\n2. **Token Savings Potential**:")
    movement_tools = [t for t in analyses if any(
        keyword in t['name'] for keyword in 
        ['move', 'strafe', 'turn', 'stand', 'sit']
    )]
    movement_tokens = sum(t['estimated_tokens'] for t in movement_tools)
    print(f"   • Movement-only agent: ~{movement_tokens:,} tokens")
    print(f"   • Savings vs full: ~{total_tokens - movement_tokens:,} tokens")
    print(f"   • Cost savings per 1M requests: ${((total_tokens - movement_tokens) * input_rate) / 1_000:.2f}")
    
    print("\n📝 NOTE: These are estimates based on typical tokenization patterns.")
    print("   Actual token counts may vary by 10-20% depending on the model.")
    
    # Export detailed analysis
    output_file = "tool_token_analysis.json"
    with open(output_file, 'w') as f:
        json.dump({
            "summary": {
                "total_tools": len(all_tools),
                "total_tokens": total_tokens,
                "total_json_size": total_json_size,
                "system_prompt_tokens": system_prompt_tokens,
                "total_overhead": total_overhead,
                "cost_per_request": cost_per_request
            },
            "tools": [
                {
                    "name": a["name"],
                    "tokens": a["estimated_tokens"],
                    "json_size": a["json_length"],
                    "breakdown": a["breakdown"]
                }
                for a in analyses
            ]
        }, f, indent=2)
    
    print(f"\n💾 Detailed analysis saved to: {output_file}")


if __name__ == "__main__":
    main()
