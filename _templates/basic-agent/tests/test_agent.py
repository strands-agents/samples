#!/usr/bin/env python3
"""
Basic tests for the Strands agent template
"""

import pytest
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from agent import create_agent, custom_tool_example


def test_custom_tool_example():
    """Test the custom tool example"""
    result = custom_tool_example("test input")
    assert result == "Processed: test input"


def test_agent_creation():
    """Test that the agent can be created successfully"""
    agent = create_agent()
    assert agent is not None
    assert hasattr(agent, 'system_prompt')
    assert hasattr(agent, 'tools')


def test_agent_tools():
    """Test that the agent has the expected tools"""
    agent = create_agent()
    tool_names = [tool.__name__ for tool in agent.tools]
    assert 'current_time' in tool_names
    assert 'custom_tool_example' in tool_names


if __name__ == "__main__":
    pytest.main([__file__]) 