#!/usr/bin/env python3
"""
Agent Orchestrator with Specialized Assistants

This pattern demonstrates the "Agents as Tools" architectural approach where 
specialized AI agents are wrapped as callable functions and coordinated by 
an orchestrator agent. This creates a hierarchical system that can handle 
complex, multi-domain queries efficiently.
"""

import os
from strands import Agent, tool
from strands_tools import file_write


# System prompts for specialized agents
RESEARCH_ASSISTANT_PROMPT = """You are a specialized research assistant. Focus only on providing
factual, well-sourced information in response to research questions.
Always cite your sources when possible and provide comprehensive, accurate information."""

PRODUCT_RECOMMENDATION_PROMPT = """You are a specialized product recommendation assistant.
Provide personalized product suggestions based on user preferences, needs, and budget.
Always explain your reasoning and consider factors like quality, value, and user requirements."""

TRIP_PLANNING_PROMPT = """You are a specialized travel planning assistant.
Create detailed travel itineraries based on user preferences, budget, and time constraints.
Include practical advice about transportation, accommodations, activities, and local tips."""


@tool
def research_assistant(query: str) -> str:
    """
    Process and respond to research-related queries with factual information.

    Args:
        query: A research question requiring factual information

    Returns:
        A detailed research answer with citations and sources
    """
    try:
        research_agent = Agent(
            system_prompt=RESEARCH_ASSISTANT_PROMPT,
        )
        response = research_agent(query)
        return str(response)
    except Exception as e:
        return f"Error in research assistant: {str(e)}"


@tool
def product_recommendation_assistant(query: str) -> str:
    """
    Handle product recommendation queries by suggesting appropriate products.

    Args:
        query: A product inquiry with user preferences and requirements

    Returns:
        Personalized product recommendations with detailed reasoning
    """
    try:
        product_agent = Agent(
            system_prompt=PRODUCT_RECOMMENDATION_PROMPT,
        )
        response = product_agent(query)
        return str(response)
    except Exception as e:
        return f"Error in product recommendation: {str(e)}"


@tool
def trip_planning_assistant(query: str) -> str:
    """
    Create travel itineraries and provide comprehensive travel advice.

    Args:
        query: A travel planning request with destination and preferences

    Returns:
        A detailed travel itinerary or travel advice with practical tips
    """
    try:
        travel_agent = Agent(
            system_prompt=TRIP_PLANNING_PROMPT,
        )
        response = travel_agent(query)
        return str(response)
    except Exception as e:
        return f"Error in trip planning: {str(e)}"


def create_orchestrator() -> Agent:
    """
    Create the main orchestrator agent that routes queries to specialized assistants.
    
    Returns:
        Agent: Configured orchestrator agent with specialist tools
    """
    # Define orchestrator system prompt with clear tool selection guidance
    system_prompt = """You are an intelligent orchestrator that routes queries to specialized agents:

ROUTING RULES:
- For research questions, factual information, or academic queries → Use research_assistant
- For product recommendations, shopping advice, or purchase decisions → Use product_recommendation_assistant  
- For travel planning, itineraries, or travel advice → Use trip_planning_assistant
- For file operations or saving content → Use file_write
- For simple questions not requiring specialized knowledge → Answer directly

BEHAVIOR:
- Always select the most appropriate specialist based on the user's query
- If a query spans multiple domains, call multiple specialists and synthesize their responses
- Be conversational and helpful in your responses
- Explain which specialist you're consulting when relevant

Always aim to provide the most helpful and accurate response by leveraging the appropriate specialist expertise."""

    orchestrator = Agent(
        system_prompt=system_prompt,
        tools=[
            research_assistant,
            product_recommendation_assistant,
            trip_planning_assistant,
            file_write,
        ],
    )
    
    return orchestrator


def demonstrate_sequential_workflow():
    """
    Demonstrate sequential agent communication where one agent's output feeds into another.
    """
    print("\n" + "="*60)
    print("DEMONSTRATING SEQUENTIAL AGENT WORKFLOW")
    print("="*60)
    
    topic = "sustainable tourism"
    
    # Create individual agents for sequential workflow
    research_agent = Agent(system_prompt=RESEARCH_ASSISTANT_PROMPT)
    summary_agent = Agent(
        system_prompt="""You are a summarization specialist focused on distilling complex 
        information into clear, concise summaries. Extract key points, main arguments, 
        and critical data while maintaining accuracy and clarity."""
    )
    
    print(f"\n🔍 RESEARCH AGENT working on: {topic}")
    
    try:
        # Step 1: Research agent gathers information
        research_response = research_agent(
            f"Please gather comprehensive information about {topic}."
        )
        research_text = str(research_response)
        
        print("\n✂️ SUMMARY AGENT distilling the research")
        
        # Step 2: Summary agent processes the research
        summary_response = summary_agent(
            f"Please create a concise summary of this research: {research_text}"
        )
        
        print(f"\n📋 FINAL SUMMARY:\n{summary_response}")
        
    except Exception as e:
        print(f"Error in sequential workflow: {str(e)}")


def main():
    """Main function to run the agent orchestrator interactively."""
    # Enable tool usage without consent prompts for demo
    os.environ["BYPASS_TOOL_CONSENT"] = "true"
    
    orchestrator = create_orchestrator()
    
    print("\n🎯 Agent Orchestrator with Specialized Assistants")
    print("=" * 60)
    print("I coordinate specialized agents to handle your queries:")
    print("  🔍 Research Assistant - for factual information and research")
    print("  🛍️  Product Recommendation - for shopping and product advice")
    print("  ✈️  Trip Planning - for travel itineraries and advice")
    print("\nType 'demo' to see a sequential workflow example")
    print("Type 'exit' to quit\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\nThanks for using the Agent Orchestrator! 👋")
                break
                
            if user_input.lower() == 'demo':
                demonstrate_sequential_workflow()
                continue
                
            if not user_input:
                print("Please enter a question, 'demo' for workflow example, or 'exit' to quit.")
                continue
            
            print(f"\n🤖 Orchestrator: ", end="")
            response = orchestrator(user_input)
            print(f"{response}\n")
            
        except KeyboardInterrupt:
            print("\n\nThanks for using the Agent Orchestrator! 👋")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again or type 'exit' to quit.\n")


if __name__ == "__main__":
    main() 