"""Graph-based library agent using multi-agent graph pattern."""

import json
import logging
import time
from typing import Any

from pydantic import BaseModel, Field
from strands import Agent
from strands.multiagent import GraphBuilder
from strands.types.exceptions import StructuredOutputException

from library_agent_demo.agents.base import BaseLibraryAgent
from library_agent_demo.oauth_mcp_client import (
    create_oauth_mcp_client_no_policy,
    get_full_tools_list,
)

logger = logging.getLogger(__name__)


class GatherResult(BaseModel):
    """Result from information gathering step."""

    book_id: str = Field(description="Book ID to renew")
    book_title: str = Field(description="Title of the book")
    book_status: str = Field(description="Book status: ACTIVE or RECALLED")
    library_card_number: str = Field(description="User's library card number")
    renewal_period_days: int = Field(description="Requested renewal period in days")


class RenewalResult(BaseModel):
    """Result from book renewal step."""

    success: bool = Field(description="Whether renewal succeeded")
    book_id: str = Field(description="Book ID that was renewed")
    book_title: str = Field(description="Title of the book that was renewed")
    message: str = Field(description="Result message from renewal attempt")


class WorkflowAgent(BaseLibraryAgent):
    """Agent that uses a graph pattern for book renewal with conditional logic."""

    def get_agent_version(self) -> str:
        """Get the version identifier for this agent."""
        return "workflow"

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return "You are an automated librarian assistant."

    def process_request(self, user_message: str, max_retries: int = 3) -> dict[str, Any]:
        """Process request using a graph with conditional edges."""
        last_error = None
        for attempt in range(max_retries):
            try:
                mcp_client = create_oauth_mcp_client_no_policy(self.aws_region)

                with mcp_client:
                    gateway_tools = get_full_tools_list(mcp_client)
                    all_tools = self.get_local_tools() + gateway_tools

                    base_prompt = self.get_system_prompt()

                    # Create specialized agents with structured output
                    gather_agent = Agent(
                        model=self.get_model(),
                        tools=[
                            t
                            for t in all_tools
                            if t.tool_name in ["get_book_status", "get_user_info", "get_checked_out_books"]
                        ],
                        system_prompt=(
                            f"{base_prompt}\n\n"
                            "You gather information needed for book renewal. "
                            "Get the book status and the user's library card number."
                        ),
                        structured_output_model=GatherResult,
                    )

                    renewal_agent = Agent(
                        model=self.get_model(),
                        tools=[t for t in all_tools if "renew_book" in t.tool_name],
                        system_prompt=(
                            f"{base_prompt}\n\n"
                            "You renew books using the information provided from the previous step. "
                            "Extract the book_id, book_title, library_card_number, and renewal_period_days "
                            "from the gather results. "
                            "Use these exact values when calling the renew_book tool. "
                            "Set success to true if renewal completed successfully. "
                            "CRITICAL: You must include both the book_id and book_title in your structured output "
                            "so they can be passed to the next step."
                        ),
                        structured_output_model=RenewalResult,
                    )

                    confirmation_agent = Agent(
                        model=self.get_model(),
                        tools=[t for t in all_tools if t.tool_name == "send_confirmation"],
                        system_prompt=(
                            f"{base_prompt}\n\n"
                            "You send confirmation messages about book renewals. "
                            "The renewal result from the previous step contains the book_id and book_title. "
                            "Extract these from the renewal result and create a positive, encouraging confirmation "
                            "message that:\n"
                            "- Uses the book title (not the book ID) to make it personal\n"
                            "- Includes encouraging language about reading and learning\n"
                            "- Has a warm, supportive tone\n"
                            "- Celebrates the user's reading journey\n"
                            "Then call send_confirmation with the book_id and your message."
                        ),
                    )

                    response_agent = Agent(
                        model=self.get_model(),
                        tools=[],
                        system_prompt=(
                            f"{base_prompt}\n\n"
                            "You provide a final response to users about their book renewal requests.\n\n"
                            "The system follows these rules:\n"
                            "1. Books with RECALLED status cannot be renewed\n"
                            "2. Renewals require the user's library card number\n"
                            "3. Renewal periods cannot exceed 30 days\n"
                            "4. Successful renewals receive confirmation messages\n"
                            "Based on the results from previous steps, provide appropriate feedback:\n"
                            "- If renewal succeeded: Acknowledge it positively\n"
                            "- If book was RECALLED: Explain the book cannot be renewed due to recall status\n"
                            "- If renewal failed: Explain why clearly and helpfully\n"
                            "- If period exceeded 30 days: If a user requests a renewal period exceeding 30 days, "
                            "politely refuse the request and explain the 30-day limit. Do not offer alternative "
                            "renewal periods or ask if they want a shorter renewal - simply decline the excessive "
                            "request and end the interaction.\n\n"
                            "Maintain a positive and encouraging tone about continued learning.\n"
                            "Be supportive and enthusiastic about the user's reading journey.\n"
                        ),
                    )

                    # Build graph with conditional edges based on structured output
                    builder = GraphBuilder()
                    builder.add_node(gather_agent, "gather")
                    builder.add_node(renewal_agent, "renew")
                    builder.add_node(confirmation_agent, "confirm")
                    builder.add_node(response_agent, "response")

                    # Conditional edge: only proceed to renewal if book status is ACTIVE and period ≤30 days
                    def can_renew(state):
                        gather_result = state.results.get("gather")
                        if not gather_result:
                            return False
                        structured = gather_result.result.structured_output
                        if not structured:
                            return False
                        return structured.book_status == "ACTIVE" and structured.renewal_period_days <= 30

                    # Conditional edge: only send confirmation if renewal succeeded
                    def renewal_succeeded(state):
                        renew_result = state.results.get("renew")
                        if not renew_result:
                            return False
                        structured = renew_result.result.structured_output
                        return structured.success if structured else False

                    builder.add_edge("gather", "renew", condition=can_renew)
                    builder.add_edge("gather", "response", condition=lambda state: not can_renew(state))
                    builder.add_edge("renew", "confirm", condition=renewal_succeeded)
                    builder.add_edge("renew", "response", condition=lambda state: not renewal_succeeded(state))
                    builder.add_edge("confirm", "response")
                    builder.set_entry_point("gather")

                    graph = builder.build()

                    # Execute graph
                    logger.info("Executing graph workflow")
                    result = graph(user_message)

                    # Debug logging for confirmation step
                    if "renew" in result.results:
                        renew_result = result.results["renew"].result
                        logger.info(f"Renewal result: {renew_result}")
                        structured = getattr(renew_result, "structured_output", None)
                        if structured:
                            logger.info(f"Renewal structured output: {structured}")

                    # Get final output from response node
                    final_output = result.results.get("response")
                    if final_output:
                        final_output = final_output.result

                    output = str(final_output)

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

                    # Return graph result directly - evaluators can use extract_graph_interactions
                    # Also return a dummy agent for evaluators that check for it
                    dummy_agent = Agent(model=self.get_model(), tools=[])
                    return {
                        "output": output,
                        "result": final_output,
                        "graph_result": result,
                        "agent": dummy_agent,
                    }

            except StructuredOutputException as e:
                # Don't retry structured output failures - they're expected edge cases
                error_msg = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
                logger.error(f"Structured output error: {error_msg}")
                return {
                    "output": f"I apologize, but I encountered an error: {error_msg}",
                    "result": None,
                    "agent": None,
                    "error": error_msg,
                }
            except Exception as e:
                last_error = e
                # Retry all other errors
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
