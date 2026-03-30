"""Model tone steering handler for ensuring positive tone in agent responses."""

import logging
import os
from typing import TYPE_CHECKING, Any, Literal, cast

import boto3
from botocore.config import Config
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from strands import Agent
from strands.models import BedrockModel
from strands.types.content import Message
from strands.vended_plugins.steering import Guide, ModelSteeringAction, Proceed, SteeringHandler

if TYPE_CHECKING:
    from strands import Agent as AgentType

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are reviewing final responses that will be sent to library users requesting
book renewals or asking questions. Your role is to ensure these messages maintain
a positive and encouraging tone about continued learning.

REQUIRED elements for responses:
1. MUST include explicit encouragement about continued reading and learning
2. MUST celebrate the user's engagement with books and knowledge
3. MUST use warm, supportive language that promotes the value of learning
4. MUST NOT be purely transactional or neutral in tone

A response that only states facts without encouraging language about learning is NOT acceptable.

When evaluating a response:
- REJECT responses that are purely transactional without learning encouragement
- REJECT responses that say only "Happy reading!" without mentioning learning
- ACCEPT responses that explicitly encourage continued learning and growth

Example ACCEPTABLE responses:
- "Great news! Your book has been renewed. Keep up the wonderful reading habit!"
- "Renewal complete! We're thrilled to support your learning journey."
- "I can't renew this recalled book, but keep exploring - there are many great titles!"

Example UNACCEPTABLE responses:
- "Your book has been renewed. The new due date is March 7. Happy reading!"
- "Renewal successful. Due date: March 7, 2026."

If the response lacks explicit encouragement about learning, provide specific
guidance on how to add celebratory language about the user's continued learning.
"""


class _ToneDecision(BaseModel):
    """Structured output for tone evaluation."""

    decision: Literal["proceed", "guide"] = Field(
        description="Steering decision: 'proceed' to accept, 'guide' to provide feedback"
    )
    reason: str = Field(description="Clear explanation of the decision and any guidance provided")


class ModelToneSteeringHandler(SteeringHandler):
    """Steering handler that validates model responses maintain positive tone."""

    name = "model_tone_steering"

    def __init__(self) -> None:
        """Initialize the model tone steering handler."""
        load_dotenv()
        super().__init__()

        retry_config = Config(retries={"max_attempts": 10, "mode": "standard"})
        bedrock_profile = os.environ.get("BEDROCK_PROFILE")
        boto_session = boto3.Session(profile_name=bedrock_profile) if bedrock_profile else None

        self._model = BedrockModel(
            model_id="openai.gpt-oss-120b-1:0",
            boto_client_config=retry_config,
            boto_session=boto_session,
        )
        logger.info("ModelToneSteeringHandler initialized")

    async def steer_after_model(
        self,
        *,
        agent: "AgentType",
        message: Message,
        stop_reason: Literal[
            "content_filtered",
            "end_turn",
            "guardrail_intervened",
            "interrupt",
            "max_tokens",
            "stop_sequence",
            "tool_use",
        ],
        **kwargs: Any,
    ) -> ModelSteeringAction:
        """Validate that model responses maintain positive tone."""
        if stop_reason != "end_turn":
            return Proceed(reason="Not a final response")

        content = message.get("content", [])
        text = " ".join(block.get("text", "") for block in content if block.get("text"))
        if not text:
            return Proceed(reason="No text content to evaluate")

        logger.info("Evaluating model response tone")

        steering_agent = Agent(system_prompt=SYSTEM_PROMPT, model=self._model, callback_handler=None)
        result = steering_agent(f"Evaluate this message:\n\n{text}", structured_output_model=_ToneDecision)
        decision: _ToneDecision = cast(_ToneDecision, result.structured_output)

        match decision.decision:
            case "proceed":
                logger.info("Tone check passed")
                return Proceed(reason=decision.reason)
            case "guide":
                logger.info(f"Tone check failed: {decision.reason}")
                guidance = f"""Your previous response was NOT shown to the user.
{decision.reason}
Please provide a new response."""
                return Guide(reason=guidance)
            case _:
                logger.warning("Unknown decision, defaulting to proceed")
                return Proceed(reason="Unknown decision, defaulting to proceed")
