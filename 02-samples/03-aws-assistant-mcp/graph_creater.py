from strands import Agent, tool
from strands_tools import python_repl, shell


@tool
def graph_creater(query: str) -> str:
    """
    Creates a graph for provided data

    Args:
        query: The user provided data in string format

    Returns:
        A helpful response addressing user query
    """

    response = str()

    try:

        # Create the research agent with specific capabilities
        graph_creater = Agent(
            system_prompt="""
            You are a graph creater agent. Your task is to write python code using Plotly to create graphs and execute this code in provided code environment. You MUST create a single graph, and then stop. You MUST NOT create more than one graph.
            """,
            tools=[python_repl, shell],
        )
        response = str(graph_creater(query))
        print("\n\n")

        if len(response) > 0:
            return response

        return "I apologize, but I couldn't properly analyze your question. Could you please rephrase or provide more context?"

    # Return specific error message for English queries
    except Exception as e:
        return f"Error processing your query: {str(e)}"


if __name__ == "__main__":
    graph_creater(
        """Create a bar graph of detailed breakdown of pricing per serice: Based on the detailed breakdown, here's a summary of your AWS service usage over the last 7 days:

Top Services by Total Cost:
1. Amazon Bedrock: ~$453.60 per day (primarily in us-west-2 region)
2. AWS Lambda: ~$31.82 per day (primarily in us-west-2 region)
3. Amazon OpenSearch Service: Varying costs across regions, ranging from $1.94 to $12.59 per day
4. Amazon Relational Database Service: Costs between $0.33 and $5.93 per day
5. Amazon SageMaker: Costs between $0.25 and $2.87 per day

Regions with Highest Service Usage:
- us-west-2: Highest Bedrock and Lambda usage
- us-east-1: Most diverse service usage with OpenSearch, RDS, SageMaker, and CloudWatch
- us-east-2: Moderate usage across several services

Notable Observations:
- Amazon Bedrock is your most expensive service, consistently around $453 daily
- AWS Lambda is a significant ongoing expense at about $31.82 per day
- OpenSearch Service has widespread usage across multiple regions
- SageMaker instance types are primarily t3.medium and t3.large for notebook and hosting"""
    )
