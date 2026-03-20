"""SOP agent implementation with structured Standard Operating Procedures."""

import logging
from pathlib import Path
from typing import Any

from .base import BaseLibraryAgent

logger = logging.getLogger(__name__)


class SOPAgent(BaseLibraryAgent):
    """Agent Version 3 - Agent SOP.

    This agent uses structured Standard Operating Procedures following the Strands SOP framework.
    The SOP provides detailed procedural guidance for each behavioral requirement and includes
    comprehensive workflow steps, constraints, and error handling procedures.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the SOP agent."""
        super().__init__(**kwargs)
        logger.info("SOPAgent initialized")

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        # Load the SOP content from the markdown file
        sop_path = Path(__file__).parent / "library_book_renewal.sop.md"

        with open(sop_path, encoding="utf-8") as f:
            sop_content = f.read()
        return f"""You are an automated librarian assistant that follows structured Standard Operating Procedures.

{sop_content}

IMPORTANT: Follow the SOP steps exactly as specified. Pay special attention to the constraints to ensure \
compliance with all library policies and behavioral requirements."""

    def get_agent_version(self) -> str:
        """Get the version identifier for this agent."""
        return "sop"
