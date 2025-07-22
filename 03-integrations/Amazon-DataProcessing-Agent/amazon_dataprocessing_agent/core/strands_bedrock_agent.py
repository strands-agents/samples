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

"""Bedrock agent for handling interactions with Amazon Bedrock models."""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

import streamlit as st
from botocore.exceptions import (ConnectTimeoutError, EndpointConnectionError,
                                 ReadTimeoutError)
from strands.models import BedrockModel
from urllib3.exceptions import ReadTimeoutError as Urllib3ReadTimeoutError

# Set up logging
logger = logging.getLogger(__name__)


class StrandsBedrockAgent:
    """Class to handle interactions with Amazon Bedrock models"""

    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 2  # seconds

    def __init__(
        self,
        model_id: str = "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        region: str = "us-east-1",
        max_tokens: int = 8000,
        temperature: float = 1.0,
        streaming: bool = True,
    ):
        """Initialize the Bedrock agent with model parameters"""
        self.model_id = model_id
        self.region = region
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.streaming = streaming
        self.model = BedrockModel(
            model_id=model_id,
            region_name=region,
            max_tokens=max_tokens,
            temperature=temperature,
            streaming=streaming,
            cache_prompt="default",
            cache_tools="default",
            additional_request_fields={
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": 2048,  # Reduced thinking budget for faster responses
                }
            },
        )

    def call_agent_with_retry(
        self,
        agent: Callable,
        prompt: str,
        messages: Optional[List[Dict[str, Any]]] = None,
        stream_callback: Optional[Callable] = None,
        max_retries: int = MAX_RETRIES,
        initial_delay: int = INITIAL_RETRY_DELAY,
    ) -> Any:
        """Call the agent with retry logic for handling transient errors"""
        retry_delay = initial_delay
        last_exception = None

        for attempt in range(max_retries):
            try:
                if self.streaming and stream_callback:
                    if messages:
                        return agent(
                            prompt,
                            messages=messages,
                            stream=True,
                            callback_handler=stream_callback,
                        )
                    else:
                        return agent(
                            prompt, stream=True, callback_handler=stream_callback
                        )
                else:
                    if messages:
                        return agent(prompt, messages=messages)
                    else:
                        return agent(prompt)

            except (
                ReadTimeoutError,
                ConnectTimeoutError,
                EndpointConnectionError,
                Urllib3ReadTimeoutError,
            ) as e:
                # Handle specific AWS connection timeout errors
                last_exception = e
                logger.warning(
                    f"AWS connection timeout on attempt {attempt + 1}: {str(e)}"
                )

                if attempt < max_retries - 1:
                    st.warning(
                        f"🔄 Connection timeout, retrying in {retry_delay} seconds (attempt {attempt+1}/{max_retries})..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    # Final attempt failed, show user-friendly error
                    error_msg = "Unable to connect to AWS Bedrock service after multiple attempts. Please check your internet connection and try again."
                    logger.error(f"All retry attempts failed: {str(e)}")
                    raise Exception(error_msg) from e

            except Exception as e:
                last_exception = e
                error_str = str(e).lower()

                # Check if it's a retryable error
                if (
                    "modelstreamerrorexception" in error_str
                    or "throttling" in error_str
                    or "timeout" in error_str
                    or "unexpected error" in error_str
                    or "read timed out" in error_str
                    or "connection pool" in error_str
                    or "awshttpsconnectionpool" in error_str
                ):
                    logger.warning(
                        f"Retryable error on attempt {attempt + 1}: {str(e)}"
                    )

                    if attempt < max_retries - 1:
                        st.warning(
                            f"🔄 Temporary service issue, retrying in {retry_delay} seconds (attempt {attempt+1}/{max_retries})..."
                        )
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        # Final attempt failed, show user-friendly error
                        error_msg = "Service temporarily unavailable after multiple attempts. Please try again in a few moments."
                        logger.error(f"All retry attempts failed: {str(e)}")
                        raise Exception(error_msg) from e

                # Non-retryable error, log and re-raise immediately
                logger.error(f"Non-retryable error: {str(e)}")
                raise last_exception
