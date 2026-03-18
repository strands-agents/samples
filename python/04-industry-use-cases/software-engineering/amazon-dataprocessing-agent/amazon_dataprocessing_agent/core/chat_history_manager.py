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

"""Chat history management for the DataProcessing Agent."""

from datetime import datetime
from typing import Any, Dict, List

import streamlit as st

from ..config.constants import MAX_CONTEXT_MESSAGES


class ChatHistoryManager:
    """Manage chat history with context window limits"""

    @staticmethod
    def add_message(role: str, content: str, thinking: str = ""):
        """Add a message to chat history"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }

        if thinking:
            message["thinking"] = thinking

        st.session_state.chat_history.append(message)

    @staticmethod
    def get_context_messages() -> List[Dict[str, Any]]:
        """Get the last N messages for context, formatted for the model"""
        # Get the last MAX_CONTEXT_MESSAGES messages
        recent_messages = st.session_state.chat_history[-MAX_CONTEXT_MESSAGES:]

        # Format for the model (only user and assistant messages)
        formatted_messages = []
        for msg in recent_messages:
            if msg["role"] in ["user", "assistant"]:
                # Convert string content to list format for Bedrock
                content = (
                    [{"text": msg["content"]}]
                    if isinstance(msg["content"], str)
                    else msg["content"]
                )
                formatted_messages.append({"role": msg["role"], "content": content})

        return formatted_messages

    @staticmethod
    def get_context_info() -> str:
        """Get information about current context window usage"""
        total_messages = len(st.session_state.chat_history)
        context_messages = min(total_messages, MAX_CONTEXT_MESSAGES)

        if total_messages > MAX_CONTEXT_MESSAGES:
            return f"📝 Using last {context_messages} of {total_messages} messages for context"
        else:
            return f"📝 Using all {total_messages} messages for context"

    @staticmethod
    def clear_history():
        """Clear chat history"""
        st.session_state.chat_history = []
        st.session_state.show_thinking = {}
