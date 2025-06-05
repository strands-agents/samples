import logging
import asyncio
from typing import Any
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
)


PUBLIC_AGENT_CARD_PATH = "/.well-known/agent.json"
EXTENDED_AGENT_CARD_PATH = "/agent/authenticatedExtendedCard"


class InteractiveA2AClient:
    def __init__(self, base_url: str = "http://localhost:10000"):
        self.base_url = base_url
        self.client: A2AClient | None = None
        self.httpx_client: httpx.AsyncClient | None = None
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """Initialize the client with agent card resolution"""
        logging.basicConfig(level=logging.INFO)

        timeout = httpx.Timeout(60.0, read=60.0, write=60.0, connect=10.0)
        self.httpx_client = httpx.AsyncClient(timeout=timeout)

        # Initialize A2ACardResolver
        resolver = A2ACardResolver(
            httpx_client=self.httpx_client,
            base_url=self.base_url,
        )

        # Fetch Public Agent Card and Initialize Client
        final_agent_card_to_use: AgentCard | None = None

        try:
            self.logger.info(
                f"Attempting to fetch public agent card from: {self.base_url}{PUBLIC_AGENT_CARD_PATH}"
            )
            _public_card = await resolver.get_agent_card()
            self.logger.info("Successfully fetched public agent card")
            final_agent_card_to_use = _public_card

            if _public_card.supportsAuthenticatedExtendedCard:
                try:
                    self.logger.info(
                        "Attempting to fetch authenticated extended card..."
                    )
                    auth_headers_dict = {
                        "Authorization": "Bearer dummy-token-for-extended-card"
                    }
                    _extended_card = await resolver.get_agent_card(
                        relative_card_path=EXTENDED_AGENT_CARD_PATH,
                        http_kwargs={"headers": auth_headers_dict},
                    )
                    self.logger.info(
                        "Successfully fetched authenticated extended agent card"
                    )
                    final_agent_card_to_use = _extended_card
                except Exception as e_extended:
                    self.logger.warning(
                        f"Failed to fetch extended agent card: {e_extended}. Using public card."
                    )

        except Exception as e:
            self.logger.error(f"Critical error fetching public agent card: {e}")
            raise RuntimeError("Failed to fetch the public agent card.") from e

        self.client = A2AClient(
            httpx_client=self.httpx_client, agent_card=final_agent_card_to_use
        )
        self.logger.info("A2AClient initialized and ready for interactive use.")

    async def send_message(self, user_input: str, streaming: bool = False):
        """Send a message and return the response"""
        if not self.client:
            raise RuntimeError("Client not initialized. Call initialize() first.")

        send_message_payload: dict[str, Any] = {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": user_input}],
                "messageId": uuid4().hex,
            },
        }

        request = SendMessageRequest(
            id=str(uuid4()), params=MessageSendParams(**send_message_payload)
        )
        return await self.client.send_message(request)

    async def interactive_loop(self):
        """Run an interactive terminal session"""
        print("\n🤖 A2A Interactive Client")
        print("Commands:")
        print("  - Type your message and press Enter")
        print("  - 'stream: <message>' for streaming response")
        print("  - 'quit' or 'exit' to stop")
        print("  - 'help' for this message")
        print("-" * 50)

        while True:
            try:
                user_input = input("\n💬 You: ").strip()

                if user_input.lower() in ["quit", "exit", "q"]:
                    print("👋 Goodbye!")
                    break

                if user_input.lower() == "help":
                    print("\nCommands:")
                    print("  - Type your message and press Enter")
                    print("  - 'stream: <message>' for streaming response")
                    print("  - 'quit' or 'exit' to stop")
                    continue

                if not user_input:
                    continue

                print("🔄 Sending message...")
                response = await self.send_message(user_input)
                print(
                    f"🤖 Agent: {response.model_dump(mode='json', exclude_none=True)}"
                )

            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                self.logger.error(f"Error in interactive loop: {e}", exc_info=True)

    async def cleanup(self):
        """Clean up resources"""
        if self.httpx_client:
            await self.httpx_client.aclose()


async def main():
    client = InteractiveA2AClient()

    try:
        await client.initialize()
        await client.interactive_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
