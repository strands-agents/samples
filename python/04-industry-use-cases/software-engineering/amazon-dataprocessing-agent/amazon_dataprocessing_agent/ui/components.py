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

"""UI components and rendering for the DataProcessing Agent."""

import json
import os
from datetime import datetime

import streamlit as st

from amazon_dataprocessing_agent.config.constants import PAGE_STYLE
from amazon_dataprocessing_agent.core.chat_history_manager import \
    ChatHistoryManager

# Constants for model parameters
TEMPERATURE = 1.0
MAX_TOKENS = 4000


class UIComponents:
    """Class to handle UI components and rendering"""

    @staticmethod
    def setup_page():
        """Set up the page configuration and styling"""
        st.set_page_config(
            page_title="Data Processing MCP Agent",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        # Apply custom CSS
        st.markdown(PAGE_STYLE, unsafe_allow_html=True)

        # Main header
        st.markdown(
            '<h1 class="main-header">🤖 Data Processing MCP Agent</h1>',
            unsafe_allow_html=True,
        )

    @staticmethod
    def render_sidebar(agent_manager):
        """Render the sidebar with controls"""
        with st.sidebar:
            st.markdown("### 🛠️ Data Processing MCP Agent")
            st.markdown("*Powered by AWS Glue, EMR and Athena with Claude model*")

            # Show initialization status
            if st.session_state.initialized:
                st.success("✅ Agent is ready!")

                # Display usage statistics
                st.markdown("### 📊 Usage Statistics")

                # Parse token information consistently
                input_tokens = 0
                output_tokens = 0

                if (
                    isinstance(st.session_state.accumulated_tokens, str)
                    and "Input Token" in st.session_state.accumulated_tokens
                ):
                    tokens_str = st.session_state.accumulated_tokens
                    input_tokens = int(
                        tokens_str.split("Input Token: ")[1].split(",")[0].strip()
                    )
                    output_tokens = int(tokens_str.split("Output Token: ")[1].strip())
                elif isinstance(st.session_state.accumulated_tokens, (int, float)):
                    # When only total is available, show it as input tokens for consistency
                    input_tokens = int(st.session_state.accumulated_tokens)
                    output_tokens = 0

                # Display tokens side by side
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📥 Input", f"{input_tokens:,}")
                with col2:
                    st.metric("📤 Output", f"{output_tokens:,}")

                st.metric("💰 LLM Cost", f"${st.session_state.accumulated_cost:.3f}")
            else:
                st.warning("⚠️ Agent not initialized")

            st.markdown("---")

            # Agent Configuration
            st.markdown("### ⚙️ Agent Configuration")

            model_options = {
                "Claude-3.7 Sonnet": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                "Claude-4 Sonnet": "us.anthropic.claude-sonnet-4-20250514-v1:0",
            }

            selected_model = st.selectbox(
                "🤖 Model", list(model_options.keys()), index=0
            )
            st.session_state.bedrock_model_id = model_options[selected_model]
            st.session_state.streaming = True

            # Initialize button
            if st.button(
                "🚀 Initialize Agent", type="primary", use_container_width=True
            ):
                with st.spinner("🔄 Connecting to DataProcessing MCP Server..."):
                    success = agent_manager.initialize_agent(
                        model_id=st.session_state.bedrock_model_id,
                        region=os.getenv("AWS_REGION", "us-east-1"),
                        max_tokens=MAX_TOKENS,
                        temperature=TEMPERATURE,
                        streaming=st.session_state.streaming,
                    )

                    if success:
                        st.session_state.initialized = True
                        st.session_state.agent = agent_manager.agent
                        st.session_state.dataprocessing_mcp_client = (
                            agent_manager.mcp_client
                        )
                        st.success("🔥 Agent initialized successfully!")
                        st.rerun()

            # Context info
            if st.session_state.chat_history:
                context_info = ChatHistoryManager.get_context_info()
                st.info(context_info)

            # Control buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Clear History", use_container_width=True):
                    ChatHistoryManager.clear_history()
                    st.rerun()

            with col2:
                if st.session_state.chat_history:
                    chat_export = json.dumps(st.session_state.chat_history, indent=2)
                    st.download_button(
                        "📥 Export Chat",
                        chat_export,
                        "chat_history.json",
                        "application/json",
                        use_container_width=True,
                    )

    @staticmethod
    def render_chat_interface(agent_manager):
        """Render the chat interface"""
        # Display chat history
        if st.session_state.chat_history:
            for i, message in enumerate(st.session_state.chat_history):
                if message["role"] == "user":
                    timestamp = datetime.fromisoformat(message["timestamp"]).strftime(
                        "%I:%M %p"
                    )
                    with st.chat_message("user"):
                        st.markdown(f"**{timestamp}**")
                        st.markdown(message["content"])
                else:
                    timestamp = datetime.fromisoformat(message["timestamp"]).strftime(
                        "%I:%M %p"
                    )
                    with st.chat_message("assistant"):
                        st.markdown(f"**{timestamp}**")
                        st.markdown(message["content"])

                        # Show thinking steps if available
                        if "thinking" in message and message["thinking"]:
                            if i not in st.session_state.show_thinking:
                                st.session_state.show_thinking[i] = False

                            toggle_text = (
                                "🧠 Hide Agent Statistics"
                                if st.session_state.show_thinking[i]
                                else "🧠 Show Agent Statistics"
                            )

                            if st.button(
                                toggle_text,
                                key=f"thinking_toggle_{i}",
                                type="secondary",
                            ):
                                st.session_state.show_thinking[i] = (
                                    not st.session_state.show_thinking[i]
                                )
                                st.rerun()

                            if st.session_state.show_thinking[i]:
                                st.code(message["thinking"], language="text")

        # Chat input
        if st.session_state.chat_history:
            context_info = ChatHistoryManager.get_context_info()
            st.info(context_info)

        col1, col2 = st.columns([5, 1])

        with col1:
            user_input = st.text_input(
                "Type your message:",
                key="chat_input",
                placeholder=(
                    "Ask me about data processing, fraud detection, or anything else..."
                    if st.session_state.initialized
                    else "Please initialize the agent first..."
                ),
                label_visibility="collapsed",
                disabled=st.session_state.is_processing
                or not st.session_state.initialized,
            )

        with col2:
            if st.session_state.is_processing:
                button_text = "🛑 Cancel"
                button_disabled = False
                button_type = "secondary"
            else:
                button_text = "📤 Send"
                button_disabled = (
                    not st.session_state.initialized or not user_input.strip()
                )
                button_type = "primary"

            send_button = st.button(
                button_text,
                type=button_type,
                use_container_width=True,
                disabled=button_disabled,
            )

        # Process message
        if send_button:
            if st.session_state.is_processing:
                st.session_state.cancel_requested = True
                st.session_state.is_processing = False
                st.warning("🛑 Request cancelled by user")
                st.rerun()
            elif user_input.strip():
                UIComponents._process_user_message(user_input.strip(), agent_manager)

    @staticmethod
    def _process_user_message(user_input: str, agent_manager):
        """Process user message with real-time streaming"""
        st.session_state.is_processing = True

        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(user_input)

        # Add user message to history
        ChatHistoryManager.add_message("user", user_input)

        # Check if agent is initialized
        if not st.session_state.initialized or not agent_manager.agent:
            with st.chat_message("assistant"):
                st.error(
                    "❌ Agent not initialized. Please initialize the agent first using the sidebar."
                )
            ChatHistoryManager.add_message(
                "assistant",
                "❌ Agent not initialized. Please initialize the agent first using the sidebar.",
            )
            st.session_state.is_processing = False
            st.rerun()
            return

        try:
            if st.session_state.streaming:
                # Process the message with real-time streaming
                response = agent_manager.process_message_with_streaming(user_input)
            else:
                # Process without streaming
                with st.spinner("🤖 Processing your request..."):
                    response = agent_manager.process_message(user_input)

                # Display non-streaming response
                with st.chat_message("assistant"):
                    st.markdown(response["content"])

            # Add agent response to history
            ChatHistoryManager.add_message(
                "assistant", response["content"], response["thinking"]
            )

        except Exception as e:
            # Provide user-friendly error messages
            error_str = str(e).lower()
            if (
                "unable to connect to aws bedrock" in error_str
                or "connection timeout" in error_str
            ):
                error_msg = "🔌 I'm having trouble connecting to the AI service. This is usually temporary - please try your request again in a moment."
            elif "service temporarily unavailable" in error_str:
                error_msg = "⏳ The AI service is temporarily busy. Please wait a moment and try again."
            elif "throttling" in error_str:
                error_msg = "🚦 The service is currently experiencing high demand. Please wait a moment before trying again."
            else:
                error_msg = f"❌ I encountered an unexpected error while processing your request. Please try again or contact support if the issue persists."

            with st.chat_message("assistant"):
                st.error(error_msg)

                # Show a retry button for connection-related errors
                if any(
                    keyword in error_str
                    for keyword in [
                        "connection",
                        "timeout",
                        "unavailable",
                        "throttling",
                    ]
                ):
                    if st.button(
                        "🔄 Retry Request",
                        key=f"retry_{len(st.session_state.chat_history)}",
                        type="secondary",
                    ):
                        # Retry the same request
                        UIComponents._process_user_message(user_input, agent_manager)
                        return

            # Add error message to history
            ChatHistoryManager.add_message("assistant", error_msg)

        finally:
            # Reset processing state
            st.session_state.is_processing = False
            st.rerun()
