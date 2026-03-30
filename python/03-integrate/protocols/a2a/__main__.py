import click
from agent import StrandAgent

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentAuthentication,
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)

from agent_executor import StrandsAgentExecutor


@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10000)
def main(host: str, port: int):
    request_handler = DefaultRequestHandler(
        agent_executor=StrandsAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=get_agent_card(host, port), http_handler=request_handler
    )
    import uvicorn

    uvicorn.run(server.build(), host=host, port=port)


def get_agent_card(host: str, port: int):
    """Returns the Agent Card for the Currency Agent."""
    capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
    skill = AgentSkill(
        id="search_aws_docs",
        name="AWS Documentation search",
        description="Search AWS documentation for topics related to AWS services.",
        tags=["AWS Documentation researcher"],
        examples=[
            "What is Amazon Bedrock?",
            "What is Amazon Bedrock pricing model?",
            "How to enable AWS lambda trigger from Amazon S3?",
        ],
    )
    return AgentCard(
        name="AWS Documentation researcher",
        description="Helps with queries related to AWS services.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=StrandAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=StrandAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill],
        authentication=AgentAuthentication(schemes=["public"]),
    )


if __name__ == "__main__":
    main()
