"""Steering agent implementation with advanced behavioral control mechanisms."""

import logging
from typing import Any

from ..oauth_mcp_client import create_oauth_mcp_client
from ..steering.confirmation_tone_steering_handler import ConfirmationToneSteeringHandler
from ..steering.confirmation_workflow_steering_handler import ConfirmationWorkflowSteeringHandler
from ..steering.model_tone_steering_handler import ModelToneSteeringHandler
from ..steering.renewal_workflow_steering_handler import RenewalWorkflowSteeringHandler
from .base import BaseLibraryAgent

logger = logging.getLogger(__name__)


class SteeringAgent(BaseLibraryAgent):
    """Agent Version 4 - Steering Providers and AgentCore Policy.

    This agent uses advanced control mechanisms including:
    1. RenewalWorkflowSteeringHandler - validates workflow adherence and input validation using built-in ledger
    2. ConfirmationWorkflowSteeringHandler - blocks confirmations without successful renewals
    3. ConfirmationToneSteeringHandler - ensures positive tone in confirmation messages
    4. ConfirmationRequiredModelSteeringHandler - ensures confirmations are sent before final response
    5. AgentCore Policy - enforces parameter constraints through gateway
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the steering agent with all steering providers."""
        super().__init__(**kwargs)

        self.renewal_workflow_handler = RenewalWorkflowSteeringHandler()
        self.confirmation_workflow_handler = ConfirmationWorkflowSteeringHandler()
        self.confirmation_tone_handler = ConfirmationToneSteeringHandler()
        self.model_tone_handler = ModelToneSteeringHandler()

        logger.info("SteeringAgent initialized with all steering handlers")

    def get_mcp_client(self) -> Any:
        """Use policy gateway for steering agent."""
        return create_oauth_mcp_client(
            gateway_stack_name="LibraryAgentGatewayStack",
            auth_stack_name="LibraryAgentAuthStack",
            aws_region=self.aws_region,
        )

    def get_plugins(self) -> list[Any]:
        """Return steering handlers as plugins."""
        return [
            self.renewal_workflow_handler,
            self.confirmation_workflow_handler,
            self.confirmation_tone_handler,
            self.model_tone_handler,
        ]

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return """You are an automated librarian assistant.
You maintain a positive and encouraging tone about continued learning.
You are supportive and enthusiastic about the user's reading journey.

The system includes behavioral controls to guide you. When a tool call is cancelled with guidance,
follow the instructions and retry the tool call as directed.

Follow these rules when asked to renew a book:

1. Use your tools to gather the information you need rather than asking the user for any additional information.

2. Books cannot be renewed for longer than 30 days.

3. Recalled books cannot be renewed.

4. If a user requests a renewal that cannot be fulfilled (period exceeding 30 days, recalled book),
   politely refuse the request and explain why. Do not offer alternative renewals.

5. Send a confirmation message only after successfully renewing a book."""

    def get_agent_version(self) -> str:
        """Get the version identifier for this agent."""
        return "steering"
