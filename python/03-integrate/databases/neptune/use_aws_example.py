
import argparse
import os
from strands import Agent
from strands.models import BedrockModel
from strands_tools import use_aws
from dotenv import load_dotenv

load_dotenv()


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Amazon Neptune agent using strands Agent use_aws tool")
    parser.add_argument("prompt", help="Prompt to send to the agent")

    # Parse arguments
    args = parser.parse_args()

    agent = Agent(
        model=BedrockModel(model_id="anthropic.claude-3-5-sonnet-20240620-v1:0"),
        tools=[use_aws],
    )

    agent.tool.use_aws(service_name="neptune-graph", operation_name="execute_query", 
                    parameters={"query": "", "language":"OPEN_CYPHER"}, region="us-west-2", 
                    graph_id=os.getenv("NEPTUNE_GRAPH_IDENTIFIER"))

    agent(args.prompt)

if __name__ == "__main__":
    main()
