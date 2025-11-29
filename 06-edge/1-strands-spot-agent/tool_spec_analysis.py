#!/usr/bin/env python3
"""
Analyze the token cost of tool specifications for Boston Dynamics Spot tools.

This script examines the tool definitions to understand their token overhead.
"""

import os
import json
from dotenv import load_dotenv
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
from strands_tools import think

# Load environment variables
load_dotenv()

def estimate_tokens(text):
    """Rough estimation of tokens (approximately 4 characters per token)."""
    return len(text) // 4

def analyze_tool(tool):
    """Analyze a single tool's specification."""
    tool_info = {
        "name": tool.__name__,
        "docstring": tool.__doc__ or "",
        "signature": str(tool.__annotations__) if hasattr(tool, "__annotations__") else "",
    }
    
    # Estimate tokens for each component
    name_tokens = estimate_tokens(tool_info["name"])
    doc_tokens = estimate_tokens(tool_info["docstring"])
    sig_tokens = estimate_tokens(tool_info["signature"])
    
    # Tool specification includes name, description, and parameters
    # In practice, the framework likely creates a JSON schema
    total_estimated = name_tokens + doc_tokens + sig_tokens + 20  # overhead
    
    return {
        "name": tool_info["name"],
        "docstring_length": len(tool_info["docstring"]),
        "signature_length": len(tool_info["signature"]),
        "estimated_tokens": total_estimated,
        "components": {
            "name": name_tokens,
            "docstring": doc_tokens,
            "signature": sig_tokens,
            "overhead": 20
        }
    }

def main():
    """Analyze all tools."""
    print("🔍 Boston Dynamics Spot Tools - Token Specification Analysis")
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
    
    additional_tools = [think]
    
    all_tools = robot_tools + additional_tools
    
    print(f"\n📊 Analyzing {len(all_tools)} tools:")
    print(f"   • Robot control tools: {len(robot_tools)}")
    print(f"   • Additional tools: {len(additional_tools)}")
    
    # Analyze each tool
    tool_analyses = []
    total_tokens = 0
    
    print("\n🔧 Tool-by-Tool Analysis:")
    print("-" * 60)
    
    for tool in all_tools:
        analysis = analyze_tool(tool)
        tool_analyses.append(analysis)
        total_tokens += analysis["estimated_tokens"]
        
        print(f"\n{analysis['name']}:")
        print(f"   • Docstring: {analysis['docstring_length']} chars")
        print(f"   • Signature: {analysis['signature_length']} chars")
        print(f"   • Estimated tokens: ~{analysis['estimated_tokens']}")
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("📈 SUMMARY STATISTICS")
    print("=" * 60)
    
    avg_tokens = total_tokens // len(all_tools)
    
    print(f"\n🎯 Total estimated tool specification tokens: ~{total_tokens:,}")
    print(f"   • Average per tool: ~{avg_tokens}")
    print(f"   • Robot tools subtotal: ~{sum(a['estimated_tokens'] for a in tool_analyses[:len(robot_tools)]):,}")
    print(f"   • Additional tools subtotal: ~{sum(a['estimated_tokens'] for a in tool_analyses[len(robot_tools):]):,}")
    
    # Find largest tools
    sorted_tools = sorted(tool_analyses, key=lambda x: x['estimated_tokens'], reverse=True)
    
    print("\n🏆 Top 5 Largest Tools (by token count):")
    for i, tool in enumerate(sorted_tools[:5], 1):
        print(f"   {i}. {tool['name']}: ~{tool['estimated_tokens']} tokens")
    
    # Token overhead breakdown
    print("\n💡 TOKEN OVERHEAD INSIGHTS:")
    print("-" * 60)
    print(f"\n1. Base Cost:")
    print(f"   • Loading all {len(all_tools)} tools adds ~{total_tokens:,} tokens to EVERY request")
    print(f"   • This is before any user input or agent response")
    
    print(f"\n2. Per-Tool Cost:")
    print(f"   • Average tool specification: ~{avg_tokens} tokens")
    print(f"   • Minimum tool size: ~{min(t['estimated_tokens'] for t in tool_analyses)} tokens")
    print(f"   • Maximum tool size: ~{max(t['estimated_tokens'] for t in tool_analyses)} tokens")
    
    print(f"\n3. Optimization Opportunities:")
    print(f"   • Remove unused tools to save tokens")
    print(f"   • Group related tools into task-specific agents")
    print(f"   • Consider lazy loading for rarely used tools")
    
    # Cost impact
    input_rate = 0.003  # $3 per 1M input tokens (Claude Sonnet)
    
    print(f"\n💰 COST IMPACT (at ${input_rate:.3f} per 1K input tokens):")
    cost_per_request = (total_tokens * input_rate) / 1000
    print(f"   • Tool overhead cost per request: ${cost_per_request:.5f}")
    print(f"   • Cost for 1,000 requests: ${cost_per_request * 1000:.2f}")
    print(f"   • Cost for 100,000 requests: ${cost_per_request * 100000:.2f}")
    print(f"   • Annual cost (1M requests): ${cost_per_request * 1000000:.2f}")
    
    print("\n📝 NOTE: These are estimates. Actual token counts may vary")
    print("   based on how the Strands framework serializes tool specs.")


if __name__ == "__main__":
    main()
