"""No instructions agent implementation with minimal system prompt."""

import logging
from typing import Any

from .base import BaseLibraryAgent

logger = logging.getLogger(__name__)


class NoInstructionsAgent(BaseLibraryAgent):
    """Agent Version 1 - No Instructions.

    This agent uses only a simple system prompt "You are an automated librarian assistant."
    with no explicit behavioral controls or validation.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the no instructions agent."""
        super().__init__(**kwargs)
        logger.info("NoInstructionsAgent initialized")

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return "You are an automated librarian assistant."

    def get_agent_version(self) -> str:
        """Get the version identifier for this agent."""
        return "no-instructions"
