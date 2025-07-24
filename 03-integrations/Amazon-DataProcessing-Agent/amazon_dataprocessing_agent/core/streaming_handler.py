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

"""Streaming handler for real-time LLM responses."""

import re
import time

import streamlit as st


class StreamingHandler:
    """Handle streaming responses from the LLM using Strands callback handlers"""

    def __init__(self):
        self.content = ""
        self.message_placeholder = None
        self.tool_placeholder = None
        self.current_tool = None
        self.tool_count = 0

    def setup_placeholders(self):
        """Setup placeholders for streaming content using Streamlit chat"""
        # Create a chat message container for the assistant
        message = st.chat_message("assistant")
        self.message_placeholder = message.empty()
        self.tool_placeholder = st.empty()

    def callback_handler(self, **kwargs):
        """Strands callback handler for streaming responses"""
        try:
            # Handle text generation events
            if "data" in kwargs:
                text_chunk = kwargs["data"]
                self.content += text_chunk
                # print(f"DEBUG: Text chunk: '{text_chunk}'")

                # Update UI with streaming content
                if self.message_placeholder:
                    self.message_placeholder.markdown(
                        self._sanitize_markdown(self.content) + "\n"
                    )

            # Handle tool usage events
            if "current_tool_use" in kwargs and kwargs["current_tool_use"].get("name"):
                tool_name = kwargs["current_tool_use"]["name"]
                if tool_name != self.current_tool:
                    self.current_tool = tool_name
                    self.tool_count += 1
                    print(f"DEBUG: Tool started: {tool_name}")

                    if self.tool_placeholder:
                        self.tool_placeholder.info(
                            f"🔧 **Tool #{self.tool_count}:** {tool_name} - Running..."
                        )

            # Handle completion events
            if kwargs.get("complete", False):
                print("DEBUG: Stream completed")
                if self.tool_placeholder and self.current_tool:
                    self.tool_placeholder.success(
                        f"✅ **Tool #{self.tool_count}:** {self.current_tool} - Completed!"
                    )
                    time.sleep(0.5)
                    self.tool_placeholder.empty()
                self.current_tool = None

            # Handle lifecycle events for debugging
            if kwargs.get("init_event_loop", False):
                print("DEBUG: 🔄 Event loop initialized")
            elif kwargs.get("start_event_loop", False):
                print("DEBUG: ▶️ Event loop cycle starting")
            elif kwargs.get("start", False):
                print("DEBUG: 📝 New cycle started")
            elif "message" in kwargs:
                print(
                    f"DEBUG: 📬 New message created: {kwargs['message'].get('role', 'unknown')}"
                )
            elif kwargs.get("force_stop", False):
                print(
                    f"DEBUG: 🛑 Event loop force-stopped: {kwargs.get('force_stop_reason', 'unknown reason')}"
                )

        except Exception as e:
            print(f"Streaming callback error: {str(e)}")
            import traceback

            print(f"Traceback: {traceback.format_exc()}")

    def finalize(self):
        """Finalize streaming and return content"""
        if self.message_placeholder:
            # Remove the typing indicator and show final content
            self.message_placeholder.markdown(self._sanitize_markdown(self.content))
        if self.tool_placeholder:
            self.tool_placeholder.empty()
        return self.content

    def reset(self):
        """Reset streaming state"""
        self.content = ""
        self.current_tool = None
        self.tool_count = 0

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
