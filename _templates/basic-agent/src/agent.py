#!/usr/bin/env python3
"""
Basic Strands Agent Template

This template provides a starting point for creating basic Strands agents.
Modify the system prompt, tools, and configuration as needed for your use case.
"""

from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import current_time

# Optional: Define custom tools
@tool
def custom_tool_example(input_text: str) -> str:
    """
    Example custom tool - replace with your own tools
    
    Args:
        input_text: Input text to process
        
    Returns:
        str: Processed output
    """
    return f"Processed: {input_text}"

def create_agent() -> Agent:
    """
    Create and configure the basic agent
    
    Returns:
        Agent: Configured Strands agent
    """
    # Configure the model (using default Bedrock model)
    model = BedrockModel(
        model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        region_name="us-east-1"  # Change to your preferred region
    )
    
    # Define system prompt
    system_prompt = """You are a helpful AI assistant built with Strands Agents.
    You have access to various tools to help users with their tasks.
    Always be helpful, accurate, and concise in your responses."""
    
    # Create agent with tools
    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[current_time, custom_tool_example]  # Add your tools here
    )
    
    return agent

def main():
    """Main function to run the agent"""
    agent = create_agent()
    
    print("🤖 Basic Strands Agent is ready!")
    print("Type 'exit' to quit\n")
    
    while True:
        try:
            user_input = input("> ")
            if user_input.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
            
            response = agent(user_input)
            print(f"\n{response}\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main() 