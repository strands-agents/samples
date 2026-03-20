"""Simple instruction agent implementation with behavioral rules in system prompt."""

import logging
from typing import Any

from .base import BaseLibraryAgent

logger = logging.getLogger(__name__)


class SimpleInstructionAgent(BaseLibraryAgent):
    """Agent Version 2 - Simple Instructions.

    This agent includes behavioral rules in the system prompt:
    1. Renewal workflow - verify book status != "RECALLED" and retrieve user info before renewal.
       Send confirmation message after renewal.
    2. Tool input validation - library card number must match user info in renewal request.
    3. Parameter constraints - renewal period must be ≤ 30 days.
    4. Tone adherence - maintain positive and encouraging communication about learning.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the simple instruction agent."""
        super().__init__(**kwargs)
        logger.info("SimpleInstructionAgent initialized")

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return """You are an automated librarian assistant.
You maintain a positive and encouraging tone about continued learning.
You are supportive and enthusiastic about the user's reading journey.

Follow these rules when asked to renew a book:

1. Use your tools to gather the information you need rather than asking the user for any additional information.

2. Books cannot be renewed for longer than 30 days.

3. Recalled books cannot be renewed.

4. If a user requests a renewal that cannot be fulfilled (period exceeding 30 days, recalled book),
   politely refuse the request and explain why. Do not offer alternative renewals.

5. Send a confirmation message only after successfully renewing a book."""

    def get_agent_version(self) -> str:
        """Get the version identifier for this agent."""
        return "simple"
