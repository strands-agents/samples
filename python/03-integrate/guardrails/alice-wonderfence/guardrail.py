"""Minimal WonderFence integration example for Strands agents."""

import json
import os
import uuid
from typing import Any

from strands.hooks import (
    AfterModelCallEvent,
    AfterToolCallEvent,
    BeforeModelCallEvent,
    BeforeToolCallEvent,
    HookProvider,
    HookRegistry,
)
from wonderfence_sdk.client import WonderFenceClient
from wonderfence_sdk.models import Actions, AnalysisContext

client = WonderFenceClient(provider="aws-bedrock", platform="aws", api_key=os.environ.get("ALICE_API_KEY"))


class WonderFenceViolationException(Exception):
    """Raised when content violates WonderFence safety policies."""

    pass


class WonderFenceHook(HookProvider):
    """WonderFence safety evaluation hook."""

    def __init__(self, wonderfence_client: WonderFenceClient) -> None:
        self.client = wonderfence_client

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeModelCallEvent, self.on_before_model_call)
        registry.add_callback(AfterModelCallEvent, self.on_after_model_call)
        registry.add_callback(BeforeToolCallEvent, self.on_before_tool_call)
        registry.add_callback(AfterToolCallEvent, self.on_after_tool_call)

    def _get_session_id(self, event: Any) -> str:
        """Get session ID from event or generate one."""
        if hasattr(event, "invocation_state") and event.invocation_state:
            return event.invocation_state.get("session_id", str(uuid.uuid4()))
        return str(uuid.uuid4())

    def _extract_text(self, content: Any) -> str:
        """Extract text from content (handles str, list, dict)."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts = [item.get("text", str(item)) for item in content if isinstance(item, dict)]
            return " ".join(texts) if texts else str(content)
        if isinstance(content, dict):
            return content.get("text", str(content))
        return str(content)

    def on_before_model_call(self, event: BeforeModelCallEvent) -> None:
        """Evaluate model input before sending to the model."""
        content = self._extract_text(event.agent.messages[-1].get("content", ""))
        context = AnalysisContext(session_id=self._get_session_id(event))

        result = self.client.evaluate_prompt_sync(context, prompt=content)
        if result.action == Actions.BLOCK:
            raise WonderFenceViolationException(f"Model input blocked: {result.detections}")

    def on_after_model_call(self, event: AfterModelCallEvent) -> None:
        """Evaluate model output and block/mask unsafe responses."""
        if not event.stop_response or not event.stop_response.message:
            return

        response_message = event.stop_response.message
        content = self._extract_text(response_message.get("content", ""))
        context = AnalysisContext(session_id=self._get_session_id(event))

        result = self.client.evaluate_response_sync(context, response=content)
        if result.action == Actions.BLOCK:
            raise WonderFenceViolationException(f"Model output blocked: {result.detections}")
        elif result.action == Actions.MASK and result.action_text:
            # Apply masked content
            if isinstance(response_message.get("content"), list) and response_message["content"]:
                response_message["content"][0]["text"] = result.action_text
            else:
                response_message["content"] = result.action_text

    def on_before_tool_call(self, event: BeforeToolCallEvent) -> None:
        """Evaluate tool input before execution."""
        tool_name = event.tool_use.get("name", "unknown")
        content = f"Tool: {tool_name}, Input: {json.dumps(event.tool_use.get('input', {}))}"
        context = AnalysisContext(session_id=self._get_session_id(event))

        result = self.client.evaluate_prompt_sync(context, prompt=content)

        if result.action == Actions.BLOCK:
            # print all the types (string) of detections
            detections_types = [detection.type for detection in result.detections]
            str = f"Access Denied: Tool '{tool_name}' input violates content policy. {', '.join(detections_types)}"
            print(str)
            event.cancel_tool = str

    def on_after_tool_call(self, event: AfterToolCallEvent) -> None:
        """Evaluate tool output and block/mask unsafe responses."""
        tool_name = event.tool_use.get("name", "unknown")
        result_obj = event.result
        content = self._extract_text(result_obj.get("content", result_obj) if isinstance(result_obj, dict) else result_obj)
        context = AnalysisContext(session_id=self._get_session_id(event))

        result = self.client.evaluate_response_sync(context, response=content)
        if result.action == Actions.BLOCK:
            raise WonderFenceViolationException(f"Tool output blocked for {tool_name}: {result.detections}")
        elif result.action == Actions.MASK and result.action_text:
            # Apply masked content
            if isinstance(result_obj, dict) and "content" in result_obj:
                if isinstance(result_obj["content"], list) and result_obj["content"]:
                    result_obj["content"][0]["text"] = result.action_text
                else:
                    result_obj["content"] = result.action_text
            else:
                event.result = result.action_text
