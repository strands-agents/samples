import asyncio
import logging
from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_message_payload(*, role: str = "user", text: str) -> dict[str, Any]:
    return {
        "message": {
            "role": role,
            "parts": [{"kind": "text", "text": text}],
            "messageId": uuid4().hex,
        },
    }


async def send_sync_message(message: str, base_url: str = "http://localhost:9000"):
    async with httpx.AsyncClient() as httpx_client:
        # Get agent card
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
        agent_card = await resolver.get_agent_card()

        # Create client
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)

        # Send message
        payload = create_message_payload(text=message)
        request = SendMessageRequest(
            id=str(uuid4()), params=MessageSendParams(**payload)
        )

        response = await client.send_message(request)
        logger.info(response.model_dump_json(exclude_none=True, indent=2))
        return response


asyncio.run(send_sync_message("what is 3 to the power fo 7"))
