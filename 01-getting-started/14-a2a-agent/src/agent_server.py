import logging
import sys
import click
import httpx
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryPushNotifier, InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from dotenv import load_dotenv
from agent import ConversionAgent
from agent_executor import ConversionAgentExecutor

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10000)
def main(host, port):
    """Starts the Mathematical Conversion Agent server."""
    try:
        capabilities = AgentCapabilities(streaming=False, pushNotifications=True)

        skill = AgentSkill(
            id="mathematical_conversions",
            name="Mathematical Conversions Tool",
            description="Helps with mathematical conversions and calculations",
            tags=["mathematical conversions", "calculations", "unit conversion"],
            examples=[
                "Convert 100 feet to meters",
                "What is 32 Fahrenheit in Celsius?",
            ],
        )

        agent_card = AgentCard(
            name="Mathematical Conversion Agent",
            description="Helps with mathematical conversions and calculations",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=ConversionAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=ConversionAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        timeout = httpx.Timeout(60.0, read=60.0, write=60.0, connect=10.0)
        httpx_client = httpx.AsyncClient(timeout=timeout)
        request_handler = DefaultRequestHandler(
            agent_executor=ConversionAgentExecutor(),
            task_store=InMemoryTaskStore(),
            push_notifier=InMemoryPushNotifier(httpx_client),
        )

        server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )

        uvicorn.run(server.build(), host=host, port=port)

    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
