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

"""Session state management for the DataProcessing Agent."""

import streamlit as st


class SessionState:
    """Class to manage session state initialization and access"""

    @staticmethod
    def initialize():
        """Initialize all session state variables"""
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        if "agent" not in st.session_state:
            st.session_state.agent = None

        if "initialized" not in st.session_state:
            st.session_state.initialized = False

        if "dataprocessing_mcp_client" not in st.session_state:
            st.session_state.dataprocessing_mcp_client = None

        if "agent_manager" not in st.session_state:
            st.session_state.agent_manager = None

        if "show_thinking" not in st.session_state:
            st.session_state.show_thinking = {}

        if "bedrock_model_id" not in st.session_state:
            st.session_state.bedrock_model_id = (
                "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
            )

        if "streaming" not in st.session_state:
            st.session_state.streaming = True

        if "is_processing" not in st.session_state:
            st.session_state.is_processing = False

        if "streaming_content" not in st.session_state:
            st.session_state.streaming_content = ""

        if "current_tool" not in st.session_state:
            st.session_state.current_tool = None

        if "cancel_requested" not in st.session_state:
            st.session_state.cancel_requested = False

        if "accumulated_tokens" not in st.session_state:
            st.session_state.accumulated_tokens = "Input Token: 0, Output Token: 0"

        if "accumulated_cost" not in st.session_state:
            st.session_state.accumulated_cost = 0.0

        if "accumulated_manual_cost" not in st.session_state:
            st.session_state.accumulated_manual_cost = 0.0

        if "manual_api_prep_time" not in st.session_state:
            st.session_state.manual_api_prep_time = 30  # Default value in seconds

        if "manual_engineer_cost" not in st.session_state:
            st.session_state.manual_engineer_cost = (
                100  # Default value in dollars per hour
            )

        # Initialize fraud data
        SessionState._initialize_fraud_data()

    @staticmethod
    def _initialize_fraud_data():
        """Initialize fraud data in session state"""
        if "fraud_data" not in st.session_state:
            st.session_state.fraud_data = {}
