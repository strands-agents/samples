# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""MCP Agent Manager for the DataProcessing Agent."""

import logging
import os
import re
import traceback
from typing import Any, Dict

import streamlit as st
from mcp import StdioServerParameters, stdio_client
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.tools.mcp import MCPClient

from amazon_dataprocessing_agent.tools.email_tools import \
    create_send_email_tools
from amazon_dataprocessing_agent.tools.s3_tables_tools import \
    create_s3tables_tools

from ..config.prompts import SYSTEM_PROMPT
from .strands_bedrock_agent import StrandsBedrockAgent
from .chat_history_manager import ChatHistoryManager
from .streaming_handler import StreamingHandler

logger = logging.getLogger(__name__)


class MCPAgentManager:
    """Manager class for MCP Agent functionality"""

    def __init__(self):
        """Initialize the MCP Agent Manager"""
        self.bedrock_agent = None
        self.mcp_client = None
        self.agent = None

    def initialize_agent(
        self,
        model_id: str,
        region: str,
        max_tokens: int,
        temperature: float,
        streaming: bool,
    ) -> bool:
        """Initialize the agent with MCP tools and Bedrock model"""
        try:

            # Set up MCP client for DataProcessing
            self.mcp_client = MCPClient(
                lambda: stdio_client(
                    StdioServerParameters(
                        command="uvx",
                        args=[
                            "awslabs.aws-dataprocessing-mcp-server@latest",
                            "--allow-write",
                        ],
                        env={
                            "FASTMCP_LOG_LEVEL": os.getenv(
                                "FASTMCP_LOG_LEVEL", "ERROR"
                            ),
                            "AWS_PROFILE": os.getenv("AWS_PROFILE", "dp-mcp"),
                            "AWS_REGION": region,
                        },
                    ),
                )
            )

            # Initialize the MCP client
            self.mcp_client.__enter__()

            # Get all tools
            dataprocessing_tools = self.mcp_client.list_tools_sync()
            all_tools = (
                dataprocessing_tools
                + create_send_email_tools()
                + create_s3tables_tools()
            )

            # Create the bedrock agent
            self.bedrock_agent = StrandsBedrockAgent(
                model_id=model_id,
                region=region,
                max_tokens=max_tokens,
                temperature=temperature,
                streaming=streaming,
            )

            # Create the agent
            self.agent = Agent(
                system_prompt=SYSTEM_PROMPT,
                tools=all_tools,
                model=self.bedrock_agent.model,
                conversation_manager=SlidingWindowConversationManager(
                    window_size=10,  # Maximum number of messages to keep
                    should_truncate_results=True,  # Enable truncating the tool result when a message is too large for the model's context window
                ),
            )

            return True

        except Exception as e:
            st.error(f"Error initializing agent: {str(e)}")
            import traceback

            st.code(traceback.format_exc())
            return False

    def process_message(
        self, user_input: str, streaming_container=None
    ) -> Dict[str, Any]:
        """Process a user message and return the response with thinking steps"""
        if not self.agent or not self.bedrock_agent:
            return {
                "content": "Agent not initialized. Please initialize the agent first.",
                "thinking": "Agent not initialized.",
            }

        try:
            # Get context messages (last N messages)
            context_messages = ChatHistoryManager.get_context_messages()

            # Setup streaming handler with container
            streaming_handler = StreamingHandler()

            if st.session_state.streaming and streaming_container:
                # Use the provided container for streaming
                with streaming_container:
                    streaming_handler.setup_placeholders()

                    # Call the agent with streaming
                    response = self.bedrock_agent.call_agent_with_retry(
                        self.agent,
                        user_input,
                        messages=context_messages,
                        stream_callback=streaming_handler.callback_handler,
                    )

                    # Finalize streaming
                    final_content = streaming_handler.finalize()
            else:
                # Call the agent without streaming
                response = self.bedrock_agent.call_agent_with_retry(
                    self.agent, user_input, messages=context_messages
                )
                final_content = response.content
                print(f"final_content: {final_content}")

            # Extract thinking steps from the response
            thinking = self._extract_thinking(final_content)

            # Clean the response to remove thinking steps
            cleaned_response = self._clean_response(final_content)

            # Extract and format metrics
            metrics_info = self._extract_metrics(response)

            # Combine thinking with metrics
            enhanced_thinking = self._combine_thinking_with_metrics(
                thinking, metrics_info
            )

            return {"content": cleaned_response, "thinking": enhanced_thinking}

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)

            # Provide user-friendly error messages
            error_str = str(e).lower()
            if (
                "unable to connect to aws bedrock" in error_str
                or "connection timeout" in error_str
            ):
                user_friendly_msg = "🔌 I'm having trouble connecting to the AI service. This is usually temporary - please try your request again in a moment."
            elif "service temporarily unavailable" in error_str:
                user_friendly_msg = "⏳ The AI service is temporarily busy. Please wait a moment and try again."
            elif "throttling" in error_str:
                user_friendly_msg = "🚦 The service is currently experiencing high demand. Please wait a moment before trying again."
            else:
                user_friendly_msg = f"❌ I encountered an unexpected error while processing your request. Please try again or contact support if the issue persists."

            return {
                "content": user_friendly_msg,
                "thinking": f"Technical Error Details:\n{str(e)}\n\nFull Traceback:\n{traceback.format_exc()}",
            }

    def process_message_with_streaming(self, user_input: str) -> Dict[str, Any]:
        """Process a user message with real-time streaming display"""
        if not self.agent or not self.bedrock_agent:
            return {
                "content": "Agent not initialized. Please initialize the agent first.",
                "thinking": "Agent not initialized.",
            }

        try:
            # Get context messages (last N messages)
            context_messages = ChatHistoryManager.get_context_messages()

            # Setup streaming handler
            streaming_handler = StreamingHandler()
            streaming_handler.setup_placeholders()

            print("DEBUG: About to call agent with streaming...")

            # Call the agent with streaming
            response = self.bedrock_agent.call_agent_with_retry(
                self.agent,
                user_input,
                messages=context_messages,
                stream_callback=streaming_handler.callback_handler,
            )

            print(f"DEBUG: Agent response received: {type(response)}")

            # If streaming didn't work, try to get content directly
            if streaming_handler.content:
                final_content = streaming_handler.finalize()
            else:
                print("DEBUG: No streaming content, using response.content")
                final_content = (
                    response.content if hasattr(response, "content") else str(response)
                )

                # Display the content manually if streaming failed
                if streaming_handler.message_placeholder:
                    streaming_handler.message_placeholder.markdown(final_content)

            # Extract thinking steps from the response
            thinking = self._extract_thinking(final_content)

            # Clean the response to remove thinking steps
            cleaned_response = self._clean_response(final_content)

            # Extract and format metrics
            metrics_info = self._extract_metrics(response)

            # Combine thinking with metrics
            enhanced_thinking = self._combine_thinking_with_metrics(
                thinking, metrics_info
            )

            return {"content": cleaned_response, "thinking": enhanced_thinking}

        except Exception as e:
            logger.error(
                f"Error processing message with streaming: {str(e)}", exc_info=True
            )

            # Provide user-friendly error messages
            error_str = str(e).lower()
            if (
                "unable to connect to aws bedrock" in error_str
                or "connection timeout" in error_str
            ):
                user_friendly_msg = "🔌 I'm having trouble connecting to the AI service. This is usually temporary - please try your request again in a moment."
            elif "service temporarily unavailable" in error_str:
                user_friendly_msg = "⏳ The AI service is temporarily busy. Please wait a moment and try again."
            elif "throttling" in error_str:
                user_friendly_msg = "🚦 The service is currently experiencing high demand. Please wait a moment before trying again."
            else:
                user_friendly_msg = f"❌ I encountered an unexpected error while processing your request. Please try again or contact support if the issue persists."

            # Display the user-friendly error in the streaming placeholder if available
            streaming_handler = StreamingHandler()
            if (
                hasattr(streaming_handler, "message_placeholder")
                and streaming_handler.message_placeholder
            ):
                streaming_handler.message_placeholder.error(user_friendly_msg)

            print(f"DEBUG: Exception in process_message_with_streaming: {str(e)}")
            print(f"DEBUG: Traceback: {traceback.format_exc()}")

            return {
                "content": user_friendly_msg,
                "thinking": f"Technical Error Details:\n{str(e)}\n\nFull Traceback:\n{traceback.format_exc()}",
            }

    def _extract_thinking(self, content: str) -> str:
        """Extract thinking steps from the response"""
        thinking_pattern = r"<thinking>(.*?)</thinking>"
        match = re.search(thinking_pattern, content, re.DOTALL)

        if match:
            # Ensure spaces are preserved by replacing any runs of spaces with a single space
            thinking_text = match.group(1).strip()
            # Fix potential space issues by normalizing whitespace
            thinking_text = re.sub(r"\s+", " ", thinking_text)

            # Sanitize markdown headers to prevent UI formatting issues
            thinking_text = self._sanitize_markdown(thinking_text)

            return thinking_text
        return ""

    def _clean_response(self, content: str) -> str:
        """Remove thinking steps from the response and sanitize markdown"""
        # Remove thinking steps
        cleaned = re.sub(
            r"<thinking>.*?</thinking>", "", content, flags=re.DOTALL
        ).strip()

        # Sanitize markdown headers to prevent UI formatting issues
        cleaned = self._sanitize_markdown(cleaned)

        return cleaned

    def _extract_metrics(self, response) -> Dict[str, Any]:
        """Extract metrics from the response"""
        metrics_dict = {
            "total_tokens": "N/A",
            "total_cost": "N/A",
            "execution_time": "N/A",
            "tools_used": [],
        }

        if hasattr(response, "metrics"):
            # Extract total tokens
            if hasattr(response.metrics, "accumulated_usage"):
                accumulated_usage = response.metrics.accumulated_usage
                input_token = accumulated_usage.get("inputTokens")
                output_token = accumulated_usage.get("outputTokens")
                current_tokens = (
                    f"Input Token: {input_token}, Output Token: {output_token}"
                )
                current_cost = (input_token * 0.000003) + (output_token * 0.000015)

                # Update metrics for this response
                metrics_dict["total_tokens"] = current_tokens
                metrics_dict["total_cost"] = current_cost

                # Accumulate tokens and cost in session state
                # Parse existing accumulated tokens
                existing_input = 0
                existing_output = 0
                if (
                    isinstance(st.session_state.accumulated_tokens, str)
                    and "Input Token" in st.session_state.accumulated_tokens
                ):
                    tokens_str = st.session_state.accumulated_tokens
                    existing_input = int(
                        tokens_str.split("Input Token: ")[1].split(",")[0].strip()
                    )
                    existing_output = int(tokens_str.split("Output Token: ")[1].strip())

                # Add current tokens to existing totals
                total_input = existing_input + input_token
                total_output = existing_output + output_token

                # Update accumulated values
                st.session_state.accumulated_tokens = (
                    f"Input Token: {total_input}, Output Token: {total_output}"
                )
                st.session_state.accumulated_cost += current_cost

            # Extract execution time
            if hasattr(response.metrics, "cycle_durations"):
                total_time = sum(response.metrics.cycle_durations)
                metrics_dict["execution_time"] = f"{total_time:.2f} seconds"

            # Extract tools used and calculate manual cost
            tools_used = []
            total_manual_cost = 0.0
            if hasattr(response.metrics, "tool_metrics"):
                for tool_name, tool_metrics in response.metrics.tool_metrics.items():
                    # Get tool input if available
                    print(tool_metrics)
                    tool_input = ""
                    call_count = tool_metrics.call_count

                    try:
                        input_dict = tool_metrics.tool.get("input")
                        # Extract key operation parameters
                        if "operation" in input_dict:
                            tool_input = f" - [operation: {input_dict['operation']}, tool call count: {call_count}]"
                    except Exception as e:
                        tool_input = f"input: [Error extracting input: {str(e)}]"

                    # Calculate manual cost for this tool
                    manual_cost = (st.session_state.manual_engineer_cost / 60) * (
                        (st.session_state.manual_api_prep_time / 60) * call_count
                    )
                    total_manual_cost += manual_cost

                    tools_used.append(
                        f"{tool_name}{tool_input}\n"
                        f"total execution time: {tool_metrics.total_time:.2f} seconds\n"
                    )

            metrics_dict["tools_used"] = tools_used
            metrics_dict["manual_cost"] = total_manual_cost

            # Accumulate manual cost in session state
            st.session_state.accumulated_manual_cost += total_manual_cost

        return metrics_dict

    def _sanitize_markdown(self, text: str) -> str:
        """Sanitize markdown headers and other problematic formatting"""
        if not text:
            return text

        # Convert markdown headers to bold text to prevent UI formatting issues
        # ## Header -> **Header**
        text = re.sub(r"^##\s+(.+)$", r"**\1**", text, flags=re.MULTILINE)

        # ### Header -> **Header**
        text = re.sub(r"^###\s+(.+)$", r"**\1**", text, flags=re.MULTILINE)

        # #### Header -> **Header**
        text = re.sub(r"^####\s+(.+)$", r"**\1**", text, flags=re.MULTILINE)

        # ##### Header -> **Header**
        text = re.sub(r"^#####\s+(.+)$", r"**\1**", text, flags=re.MULTILINE)

        # ###### Header -> **Header**
        text = re.sub(r"^######\s+(.+)$", r"**\1**", text, flags=re.MULTILINE)

        # # Header -> **Header** (main headers)
        text = re.sub(r"^#\s+(.+)$", r"**\1**", text, flags=re.MULTILINE)

        # Also handle headers that might be in the middle of lines
        text = re.sub(r"\n##\s+(.+)", r"\n**\1**", text)
        text = re.sub(r"\n###\s+(.+)", r"\n**\1**", text)
        text = re.sub(r"\n####\s+(.+)", r"\n**\1**", text)
        text = re.sub(r"\n#####\s+(.+)", r"\n**\1**", text)
        text = re.sub(r"\n######\s+(.+)", r"\n**\1**", text)
        text = re.sub(r"\n#\s+(.+)", r"\n**\1**", text)

        return text

    def _combine_thinking_with_metrics(
        self, thinking: str, metrics: Dict[str, Any]
    ) -> str:
        """Combine thinking steps with execution metrics"""
        # Format metrics section
        metrics_section = "\n📊 EXECUTION STATISTICS\n"
        metrics_section += f"⏱️ Execution Time: {metrics['execution_time']}\n"

        if metrics["tools_used"]:
            tool_count = len(metrics["tools_used"])
            metrics_section += f"🔧 {tool_count} Tools Used:\n"
            for i, tool in enumerate(metrics["tools_used"], 1):
                metrics_section += f"{i}. {tool}\n"
        else:
            metrics_section += f"🔧 Tools Used: None"

        metrics_section += "\n"
        # Combine thinking with metrics
        return thinking + metrics_section

    def cleanup(self):
        """Clean up resources"""
        if self.mcp_client:
            try:
                self.mcp_client.__exit__(None, None, None)
            except Exception as e:
                print(f"Error during MCP client cleanup: {str(e)}")
