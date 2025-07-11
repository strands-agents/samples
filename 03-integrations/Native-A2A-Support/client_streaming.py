import asyncio
import logging
from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendStreamingMessageRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 300 # set request timeout to 5 minutes

def create_message_payload(*, role: str = "user", text: str) -> dict[str, Any]:
    return {
        "message": {
            "role": role,
            "parts": [{"kind": "text", "text": text}],
            "messageId": uuid4().hex,
        },
    }


async def send_streaming_message(message: str, base_url: str = "http://localhost:9000"):
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as httpx_client:
        # Get agent card
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
        agent_card = await resolver.get_agent_card()

        # Create client
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)

        # Send streaming message
        payload = create_message_payload(text=message)
        request = SendStreamingMessageRequest(
            id=str(uuid4()), params=MessageSendParams(**payload)
        )

        async for event in client.send_message_streaming(request):
            logger.info(event.model_dump_json(exclude_none=True, indent=2))


asyncio.run(send_streaming_message("what is 123 * 12"))
