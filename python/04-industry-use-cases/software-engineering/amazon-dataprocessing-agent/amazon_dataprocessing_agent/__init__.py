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

"""
Amazon DataProcessing Agent

A comprehensive data processing agent for AWS services including Glue, EMR, and Athena.
"""

__version__ = "0.1.0"

from amazon_dataprocessing_agent.core.agent_manager import MCPAgentManager
from amazon_dataprocessing_agent.core.session_state import SessionState
from amazon_dataprocessing_agent.ui.components import UIComponents

__all__ = [
    "MCPAgentManager",
    "SessionState",
    "UIComponents",
]
