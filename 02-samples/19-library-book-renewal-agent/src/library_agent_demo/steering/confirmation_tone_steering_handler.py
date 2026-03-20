"""Message tone steering handler for ensuring positive tone in confirmation messages."""

import logging
import os
from typing import Any

import boto3
from botocore.config import Config
from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel
from strands.types.tools import ToolUse
from strands.vended_plugins.steering import LLMSteeringHandler, Proceed, ToolSteeringAction

logger = logging.getLogger(__name__)


class ConfirmationToneSteeringHandler(LLMSteeringHandler):
    """LLM-based steering handler for ensuring positive tone in confirmation messages.

    This handler specifically validates the message parameter of send_confirmation
    tool calls to ensure they maintain a positive and encouraging tone about
    continued learning and library usage.
    """

    name = "confirmation_tone_steering"

    def __init__(self) -> None:
        """Initialize the message tone steering handler."""
        load_dotenv()  # Load environment variables

        system_prompt = """
        You are reviewing confirmation messages that will be sent to library users after
        book renewals. Your role is to ensure these messages maintain a positive and
        encouraging tone about continued learning.

        REQUIRED elements for confirmation messages:
        1. MUST include explicit encouragement about continued reading and learning
        2. MUST celebrate the user's engagement with books and knowledge
        3. MUST use warm, supportive language that promotes the value of learning
        4. MUST NOT be purely transactional or neutral in tone

        A message that only states facts (book renewed, due date) without encouraging
        language about learning is NOT acceptable.

        When evaluating a confirmation message:
        - REJECT messages that are purely transactional without learning encouragement
        - REJECT messages that say only "Happy reading!" without mentioning learning
        - ACCEPT messages that explicitly encourage continued learning and growth

        Example ACCEPTABLE messages:
        - "Great news! Your book has been renewed. Keep up the wonderful reading habit!"
        - "Renewal complete! We're thrilled to support your learning journey."

        Example UNACCEPTABLE messages:
        - "Your book has been renewed. The new due date is March 7. Happy reading!"
        - "Renewal successful. Due date: March 7, 2026."

        If the message lacks explicit encouragement about learning, your guidance MUST:
        1. Start with "Tool call cancelled."
        2. Explain what is missing from the message
        3. Provide specific suggestions for improvement
        4. End with "Retry the send_confirmation tool with an improved message."
        """

        # Create retry configuration for throttling
        retry_config = Config(
            retries={
                "max_attempts": 10,
                "mode": "standard",
            }
        )

        # Get Bedrock-specific AWS profile from environment variable if set
        bedrock_profile = os.environ.get("BEDROCK_PROFILE")
        boto_session = None
        if bedrock_profile:
            boto_session = boto3.Session(profile_name=bedrock_profile)

        # Create the model for message tone steering
        model = BedrockModel(
            model_id="openai.gpt-oss-120b-1:0",
            boto_client_config=retry_config,
            boto_session=boto_session,
        )

        super().__init__(system_prompt=system_prompt, model=model)
        logger.info("ConfirmationToneSteeringHandler initialized")

    async def steer_before_tool(self, *, agent: Agent, tool_use: ToolUse, **kwargs: Any) -> ToolSteeringAction:
        """Evaluate confirmation messages for positive tone adherence.

        Args:
            agent: The agent attempting the tool call
            tool_use: The tool use being attempted
            **kwargs: Additional keyword arguments

        Returns:
            ToolSteeringAction indicating whether to proceed or provide tone guidance
        """
        tool_name = tool_use.get("name")

        # Only evaluate send_confirmation tool calls
        if tool_name != "send_confirmation":
            return Proceed(reason="Not a confirmation tool call")  # Let other handlers process non-confirmation tools

        logger.info("Evaluating message tone for send_confirmation tool call")

        # Use the parent LLMSteeringHandler's steer_before_tool method which will evaluate
        # the tool use against the system prompt and provide appropriate guidance
        return await super().steer_before_tool(agent=agent, tool_use=tool_use, **kwargs)
