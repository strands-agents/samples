
from strands import Agent
from strands.models import BedrockModel
from strands_tools import use_aws

agent = Agent(
    model=BedrockModel(model_id="anthropic.claude-3-5-sonnet-20240620-v1:0"),
    tools=[use_aws],
)

agent.tool.use_aws(service_name="neptune-graph", operation_name="execute_query", 
                   parameters={"query": "", "language":"OPEN_CYPHER"}, region="us-west-2", 
                   graph_id="<INSERT YOUR NEPTUNE ANALYTICS GRAPH ID HERE>")

resp = agent("Run this query: MATCH (n) RETURN n LIMIT 10")
