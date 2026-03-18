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

"""Main application entry point for the DataProcessing Agent."""

import atexit

import streamlit as st
from dotenv import load_dotenv

from amazon_dataprocessing_agent.core.agent_manager import MCPAgentManager
from amazon_dataprocessing_agent.core.session_state import SessionState
from amazon_dataprocessing_agent.ui.components import UIComponents

# Load environment variables from .env file
load_dotenv()


def cleanup():
    """Clean up resources when the app is closed"""
    if (
        "dataprocessing_mcp_client" in st.session_state
        and st.session_state.dataprocessing_mcp_client
    ):
        try:
            st.session_state.dataprocessing_mcp_client.__exit__(None, None, None)
        except Exception as e:
            print(f"Error during MCP client cleanup: {str(e)}")


def main():
    """Main application entry point"""
    # Set up the page
    UIComponents.setup_page()

    # Initialize session state
    SessionState.initialize()

    # Create or retrieve agent manager from session state
    if (
        "agent_manager" not in st.session_state
        or st.session_state.agent_manager is None
    ):
        st.session_state.agent_manager = MCPAgentManager()

    agent_manager = st.session_state.agent_manager

    # Render sidebar
    UIComponents.render_sidebar(agent_manager)

    # Render chat interface
    UIComponents.render_chat_interface(agent_manager)


if __name__ == "__main__":
    # Register cleanup handler using atexit
    atexit.register(cleanup)
    main()
