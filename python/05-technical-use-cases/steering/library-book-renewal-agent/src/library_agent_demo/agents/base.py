"""Base class for library agents with OAuth integration."""

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Any

import boto3
from aws_bedrock_token_generator import provide_token
from botocore.config import Config
from dotenv import load_dotenv
from strands import Agent, tool
from strands.models import BedrockModel, Model
from strands.models.openai import OpenAIModel

from ..oauth_mcp_client import create_oauth_mcp_client_no_policy, get_full_tools_list
from ..tools import BookStatusTool, CheckedOutBooksTool, SendConfirmationTool, UserInfoTool

logger = logging.getLogger(__name__)


class BaseLibraryAgent(ABC):
    """Base class for all library agent implementations with OAuth integration."""

    def __init__(self, aws_region: str = "us-west-2", **kwargs: Any) -> None:
        """Initialize the base agent with OAuth credentials from AWS."""
        load_dotenv()  # Load environment variables from .env file
        self.aws_region = aws_region

        # Initialize tools
        self.book_status_tool = BookStatusTool()
        self.checked_out_books_tool = CheckedOutBooksTool()
        self.send_confirmation_tool = SendConfirmationTool()
        self.user_info_tool = UserInfoTool()

        logger.info("BaseLibraryAgent initialized")

    def get_mcp_client(self) -> Any:
        """Get the MCP client for this agent. Override to use different gateway."""
        return create_oauth_mcp_client_no_policy(self.aws_region)

    def get_plugins(self) -> list[Any]:
        """Get plugins for this agent. Override to add steering handlers."""
        return []

    def process_request(self, user_message: str, max_retries: int = 3) -> dict[str, Any]:
        """Process a user request through the agent."""
        last_error = None
        for attempt in range(max_retries):
            try:
                mcp_client = self.get_mcp_client()

                with mcp_client:
                    gateway_tools = get_full_tools_list(mcp_client)
                    logger.info(f"Found gateway tools: {[tool.tool_name for tool in gateway_tools]}")

                    all_tools = self.get_local_tools() + gateway_tools
                    model = self.get_model()
                    plugins = self.get_plugins()

                    agent = Agent(
                        model=model,
                        tools=all_tools,
                        system_prompt=self.get_system_prompt(),
                        plugins=plugins if plugins else None,
                    )

                    result = agent(user_message)
                    output = str(result)

                    # Retry on empty response or malformed JSON response (likely failed tool call)
                    stripped = output.strip()
                    is_empty = not output or stripped == "" or stripped == "None"
                    is_json = False
                    try:
                        json.loads(stripped)
                        is_json = True
                    except (json.JSONDecodeError, ValueError):
                        pass
                    if is_empty or is_json:
                        logger.warning(f"Bad response (attempt {attempt + 1}/{max_retries}): {is_empty=} {is_json=}")
                        if attempt < max_retries - 1:
                            time.sleep(1)
                            continue

                    return {"output": output, "result": result, "agent": agent}

            except Exception as e:
                last_error = e
                # Retry all errors for base agent
                logger.warning(f"Retryable error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue

        error_msg = (
            f"{type(last_error).__name__}: {last_error}"
            if last_error and str(last_error)
            else (type(last_error).__name__ if last_error else "Unknown error")
        )
        logger.error(f"Max retries exceeded: {error_msg}")
        return {
            "output": f"I apologize, but I encountered an error: {error_msg}",
            "result": None,
            "agent": None,
            "error": error_msg,
            "max_retries_exceeded": True,
        }

    def get_local_tools(self) -> list[Any]:
        """Get local tools for this agent."""

        @tool
        def get_book_status(book_id: str) -> dict:
            """Get the status of a library book."""
            status = self.book_status_tool.get_status(book_id)
            return {
                "book_id": status.book_id,
                "status": status.status,
            }

        @tool
        def get_user_info() -> dict:
            """Get the current user's information."""
            user_info = self.user_info_tool.get_user_info()
            return {
                "name": user_info.name,
                "account_number": user_info.account_number,
                "library_card_number": user_info.library_card_number,
            }

        @tool
        def get_checked_out_books() -> list:
            """Get the list of books currently checked out by the user.
            Returns each book's title and book identifier (for example, ABC-098)
            """
            return self.checked_out_books_tool.get_checked_out_books()

        @tool
        def send_confirmation(book_id: str, message: str) -> str:
            """Send a personalized confirmation message to the user."""
            return self.send_confirmation_tool.send_confirmation(book_id, message)

        return [get_book_status, get_user_info, get_checked_out_books, send_confirmation]

    def get_model_id(self) -> str:
        """Get the model ID for this agent."""
        model_id = "openai.gpt-oss-120b"
        logger.info(f"Library agent using model {model_id}")
        return model_id

    def get_model(self) -> Model:
        """Create a Model instance with appropriate configuration."""
        model_id = self.get_model_id()

        # Use BedrockModel for Anthropic models
        if "anthropic" in model_id.lower():
            retry_config = Config(
                retries={
                    "max_attempts": 10,
                    "mode": "standard",
                }
            )

            bedrock_profile = os.environ.get("BEDROCK_PROFILE")
            boto_session = None
            if bedrock_profile:
                boto_session = boto3.Session(profile_name=bedrock_profile)

            return BedrockModel(
                model_id=model_id,
                boto_client_config=retry_config,
                boto_session=boto_session,
            )

        # Use OpenAIModel with Bedrock Mantle for other models
        # Generate short-term API key for Mantle endpoint
        api_key = provide_token(region=self.aws_region)

        return OpenAIModel(
            client_args={
                "api_key": api_key,
                "base_url": f"https://bedrock-mantle.{self.aws_region}.api.aws/v1",
            },
            model_id=model_id,
        )

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass

    @abstractmethod
    def get_agent_version(self) -> str:
        """Get the version identifier for this agent."""
        pass
