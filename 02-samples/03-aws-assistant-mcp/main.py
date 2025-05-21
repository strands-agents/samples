"""
# 🌐 AWS Documentaion Agent

A agent specialized in AWS docs research using MCP.

## What This Example Shows

This example demonstrates:
- Creating a research-oriented agent
- Storing research findings in memory for context preservation
- Using MCP server

Basic research query:
```
How to trigger AWS Lambda from S3?
```
"""

from aws_cost_assistant import aws_cost_assistant
from aws_documentation_researcher import aws_documentation_researcher
from graph_creater import graph_creater
from strands import Agent
from strands_tools import think

# Interactive mode when run directly

SUPERVISOR_AGENT_PROMPT = """

You are Router Agent, a sophisticated orchestrator designed to coordinate support across AWS documentation and AWS cost. Your role is to:

1. Analyze incoming queries and determine the most appropriate specialized agent to handle them:
   - AWS Cost Assistant: For queries related to AWS spend in the account
   - AWS Documentation researcher: To search AWS documentation 
   - Graph Creator: Create a graph to visualize AWS spend
   
2. Key Responsibilities:
   - Accurately classify queries
   - Route requests to the appropriate specialized agent
   - Maintain context and coordinate multi-step problems
   - Ensure cohesive responses when multiple 02-agents are needed

3. Decision Protocol:
   - If query involves questions about AWS -> AWS Documentation researcher
   - If query involves getting AWS spend -> AWS Cost Assistant and then Graph Creator to create visualization
   - If the query is not related to AWS simply refuse to answer
   
Always confirm your understanding before routing to ensure accurate assistance.


"""

supervisor_agent = Agent(
    system_prompt=SUPERVISOR_AGENT_PROMPT,
    # stream_handler=None,
    tools=[aws_documentation_researcher, graph_creater, aws_cost_assistant, think],
)


# Example usage
if __name__ == "__main__":
    print("\n📁 AWS Agent\n")
    print("Ask a question about AWS or query your AWS spend.\n\n")
    
    print("You can try following queries:")
    print("- Explain AWS Lambda triggers")
    print("- What's my AWS spending this month?")
    print("- Create a graph of my service costs")
    print("Type 'exit' to quit.")

    # Interactive loop
    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() == "exit":
                print("\nGoodbye! 👋")
                break

            response = supervisor_agent(
                user_input,
            )

            # Extract and print only the relevant content from the specialized agent's response
            content = str(response)
            print(content)

        except KeyboardInterrupt:
            print("\n\nExecution interrupted. Exiting...")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            print("Please try asking a different question.")
