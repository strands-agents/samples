"""
Strands to OpenInference Converter for Arize AI (v2.8.3-simplified)

This module provides a span processor that converts Strands telemetry data to OpenInference format.
System prompts are sourced from the STRANDS_AGENT_SYSTEM_PROMPT environment variable only.

Version History:
- v2.3.0: Fixed early return bug for OpenInference attributes
- v2.4.0: Added environment variable fallback for timing issues
- v2.5.0: (Reverted) Attempted nested format - OpenTelemetry doesn't support dict attributes
- v2.6.0: Keep flat format, add system prompt as first message in llm.input_messages
- v2.7.0: Add nested LLM data as span event for Arize UI compatibility
- v2.8.0: Add nested LLM data as special JSON attribute for Arize processing
- v2.8.1: Add "system:" prefix to prompt_template.template to match Arize format
- v2.8.1-simplified: Removed span hierarchy tracking, only use environment variable for system prompt
- v2.8.2-simplified: Filter out arize.* attributes from LLM spans
- v2.8.3-simplified: Also filter out openinference.llm attribute from LLM spans
"""

import json
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime

from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.trace import Span
from opentelemetry.trace.span import TraceState

logger = logging.getLogger(__name__)

class StrandsToOpenInferenceProcessor(SpanProcessor):
    """
    SpanProcessor that converts Strands telemetry attributes to OpenInference format.
    System prompts are sourced from the STRANDS_AGENT_SYSTEM_PROMPT environment variable.
    
    Troubleshooting:
    - Enable debug=True to see detailed logging
    - Set STRANDS_AGENT_SYSTEM_PROMPT environment variable for system prompts
    - Use get_processor_info() for diagnostic information
    """

    def __init__(self, debug: bool = False):
        """
        Initialize the processor.
        
        Args:
            debug: Whether to log detailed debug information
        """
        super().__init__()
        self.debug = debug
        self.processed_spans = set()
        self.current_cycle_id = None
        self.last_prompt_source = None  # Track where system prompt came from
        
    def _normalize_span_id(self, span_id) -> Optional[int]:
        """
        Centralized span ID normalization to handle all formats consistently.
        
        Args:
            span_id: Span ID in various formats (int, str, hex str, etc.)
            
        Returns:
            Normalized integer span ID or None if invalid
        """
        if span_id is None:
            return None
        
        if isinstance(span_id, int):
            return span_id
        
        if isinstance(span_id, str):
            try:
                if span_id.startswith('0x'):
                    return int(span_id, 16)
                else:
                    return int(span_id)
            except ValueError:
                # Log warning but don't fail - use hash as fallback
                if self.debug:
                    self._debug_log('WARN', f'Could not normalize span_id: {span_id}, using hash fallback')
                return hash(span_id) % (2**63)  # Ensure positive 64-bit int
        
        # For other types, convert to string then normalize
        return self._normalize_span_id(str(span_id))
    
    def _debug_log(self, level: str, message: str, **kwargs):
        """
        Structured debug logging with context information.
        
        Args:
            level: Log level (INFO, WARN, ERROR)
            message: Log message
            **kwargs: Additional context information
        """
        if not self.debug:
            return
        
        context = {
            'processor': 'StrandsToOpenInference',
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        
        log_message = f"[{level}] {message} | Context: {json.dumps(context, separators=(',', ':'))}"
        
        if level == 'ERROR':
            logger.error(log_message)
        elif level == 'WARN':
            logger.warning(log_message)
        else:
            logger.info(log_message)

    def on_start(self, span, parent_context=None):
        """
        Basic span start handling - no hierarchy tracking needed for environment variable approach.
        
        Args:
            span: The span that is starting
            parent_context: Optional parent context
        """
        pass

    def on_end(self, span: Span):
        """
        Enhanced span processing with deferred resolution for system prompt inheritance.
        
        Args:
            span: The span that is ending
        """
        if not hasattr(span, '_attributes') or not span._attributes:
            return

        original_attrs = dict(span._attributes)
        span_id = self._normalize_span_id(span.get_span_context().span_id)
        
        # Determine span kind early
        span_kind = self._determine_span_kind(span, original_attrs)
        
        try:
            if "event_loop.cycle_id" in original_attrs:
                self.current_cycle_id = original_attrs.get("event_loop.cycle_id")
            
            # Extract events if available
            events = []
            if hasattr(span, '_events'):
                events = span._events
            elif hasattr(span, 'events'):
                events = span.events
                
            # ALWAYS process span to ensure OpenInference attributes are added
            transformed_attrs = self._transform_attributes(original_attrs, span, events)
            span._attributes.clear()
            span._attributes.update(transformed_attrs)
            self.processed_spans.add(span_id)
            
            if self.debug:
                self._debug_log('INFO', f'Transformed span successfully',
                               span_name=span.name, original_attrs=len(original_attrs),
                               transformed_attrs=len(transformed_attrs), events=len(events))
                
        except Exception as e:
            self._debug_log('ERROR', f'Failed to transform span: {str(e)}',
                           span_name=span.name, span_id=span_id)
            logger.error(f"Failed to transform span '{span.name}': {e}", exc_info=True)
            # Restore original attributes on failure
            span._attributes.clear()
            span._attributes.update(original_attrs)


    def _transform_attributes(self, attrs: Dict[str, Any], span: Span, events: List = None) -> Dict[str, Any]:
        """
        Transform Strands attributes to OpenInference format with enhanced system prompt handling.
        """
        result = {}
        span_kind = self._determine_span_kind(span, attrs)
        result["openinference.span.kind"] = span_kind
        self._set_graph_node_attributes(span, attrs, result)
        
        # Extract messages from events if available, otherwise fall back to attributes
        if events and len(events) > 0:
            input_messages, output_messages = self._extract_messages_from_events(events)
        else:
            # Fallback to attribute-based extraction
            prompt = attrs.get("gen_ai.prompt")
            completion = attrs.get("gen_ai.completion")
            if prompt or completion:
                input_messages, output_messages = self._extract_messages_from_attributes(prompt, completion)
            else:
                input_messages, output_messages = [], []
        
        model_id = attrs.get("gen_ai.request.model")
        agent_name = attrs.get("agent.name") or attrs.get("gen_ai.agent.name")

        if model_id:
            result["llm.model_name"] = model_id
            result["gen_ai.request.model"] = model_id
            
        if agent_name:
            result["llm.system"] = "strands-agents"
            result["llm.provider"] = "strands-agents"
        
        # Handle tags (both Strands arize.tags and standard tag.tags)
        self._handle_tags(attrs, result)
        
        # Handle different span types
        if span_kind in ["LLM", "AGENT", "CHAIN"]:
            self._handle_llm_span(attrs, result, input_messages, output_messages, span)
        elif span_kind == "TOOL":
            self._handle_tool_span(attrs, result, events)
        
        # Handle token usage
        self._map_token_usage(attrs, result)
        
        # Important attributes
        important_attrs = [
            "session.id", "user.id", "llm.prompt_template.template",
            "llm.prompt_template.version", "llm.prompt_template.variables",
            "gen_ai.event.start_time", "gen_ai.event.end_time"
        ]
        
        for key in important_attrs:
            if key in attrs:
                result[key] = attrs[key]
        
        self._add_metadata(attrs, result)
        
        # Filter out arize.* attributes for LLM spans
        if span_kind == "LLM":
            result = self._filter_arize_attributes(result)
            
        return result

    def _handle_llm_span(self, attrs: Dict[str, Any], result: Dict[str, Any], 
                        input_messages: List[Dict], output_messages: List[Dict], span: Span):
        """
        Enhanced LLM span handling with multiple system prompt sources and fallback mechanisms.
        """
        
        # System prompt handling - environment variable only
        span_kind = result.get("openinference.span.kind")
        system_prompt = None
        
        if span_kind == "LLM":
            # Check environment variable for system prompt
            import os
            system_prompt = os.environ.get('STRANDS_AGENT_SYSTEM_PROMPT')
            if system_prompt:
                self.last_prompt_source = 'environment_variable'
                self._debug_log('INFO', f'Found system prompt in environment variable',
                               prompt_length=len(system_prompt))
            
            if system_prompt:
                result["llm.prompt_template.template"] = system_prompt
                self._debug_log('INFO', f'Set system prompt for LLM span',
                               source=self.last_prompt_source, 
                               prompt_length=len(system_prompt))
                
                # Add system prompt as first message if not already present
                if input_messages:
                    # Check if first message is already a system message
                    has_system_message = (input_messages[0].get('message.role') == 'system' 
                                        if input_messages else False)
                    
                    if not has_system_message:
                        # Prepend system prompt as first message
                        system_message = {
                            "message.content": system_prompt,
                            "message.role": "system"
                        }
                        input_messages = [system_message] + input_messages
                        self._debug_log('INFO', f'Added system prompt as first input message')
                else:
                    # No input messages, create with just system prompt
                    input_messages = [{
                        "message.content": system_prompt,
                        "message.role": "system"
                    }]
                    self._debug_log('INFO', f'Created input messages with system prompt')
            else:
                # Set a placeholder to ensure the attribute exists
                result["llm.prompt_template.template"] = "[System prompt not available - set STRANDS_AGENT_SYSTEM_PROMPT environment variable]"
                self._debug_log('WARN', f'No system prompt found for LLM span, using placeholder')
        
        # Create message arrays with potentially updated input_messages
        if input_messages:
            result["llm.input_messages"] = json.dumps(input_messages, separators=(",", ":"))
            self._flatten_messages(input_messages, "llm.input_messages", result)
        
        if output_messages:
            result["llm.output_messages"] = json.dumps(output_messages, separators=(",", ":"))
            self._flatten_messages(output_messages, "llm.output_messages", result)
        
        # Handle agent tools
        if tools := (attrs.get("gen_ai.agent.tools") or attrs.get("agent.tools")):
            self._map_tools(tools, result)
        
        # Create input/output values
        self._create_input_output_values(attrs, result, input_messages, output_messages)
        
        # Map invocation parameters
        self._map_invocation_parameters(attrs, result)
        
        # Add nested LLM data as span event for Arize UI compatibility (v2.7.0)
        # Note: Use the potentially updated input_messages that includes system prompt
        if span_kind == "LLM" and system_prompt:
            # Get the updated input_messages that should now include the system prompt
            if "llm.input_messages" in result:
                try:
                    updated_input_messages = json.loads(result["llm.input_messages"])
                    self._add_arize_compatible_event(span, updated_input_messages, output_messages, system_prompt, attrs)
                except json.JSONDecodeError:
                    # Fallback to original input_messages
                    self._add_arize_compatible_event(span, input_messages, output_messages, system_prompt, attrs)
            else:
                self._add_arize_compatible_event(span, input_messages, output_messages, system_prompt, attrs)
                
        # NEW v2.8.0: Also try adding nested LLM data as JSON string attribute
        if span_kind == "LLM" and system_prompt:
            # Get the updated input_messages if available
            final_input_messages = input_messages
            if "llm.input_messages" in result:
                try:
                    final_input_messages = json.loads(result["llm.input_messages"])
                except json.JSONDecodeError:
                    final_input_messages = input_messages
            self._add_nested_llm_json_attribute(result, final_input_messages, output_messages, system_prompt, attrs)



    # Include all the other methods from the original processor with enhancements
    def _extract_messages_from_events(self, events: List) -> Tuple[List[Dict], List[Dict]]:
        """Extract input and output messages from Strands events with updated format handling."""
        input_messages = []
        output_messages = []
        
        for event in events:
            event_name = getattr(event, 'name', '') if hasattr(event, 'name') else event.get('name', '')
            event_attrs = getattr(event, 'attributes', {}) if hasattr(event, 'attributes') else event.get('attributes', {})
            
            if event_name == "gen_ai.user.message":
                content = event_attrs.get('content', '')
                message = self._parse_message_content(content, 'user')
                if message:
                    input_messages.append(message)
                    
            elif event_name == "gen_ai.assistant.message":
                content = event_attrs.get('content', '')
                message = self._parse_message_content(content, 'assistant')
                if message:
                    output_messages.append(message)
                    
            elif event_name == "gen_ai.choice":
                # Final response from the agent
                message_content = event_attrs.get('message', '')
                if message_content:
                    message = self._parse_message_content(message_content, 'assistant')
                    if message:
                        # Set finish reason if available
                        if 'finish_reason' in event_attrs:
                            message['message.finish_reason'] = event_attrs['finish_reason']
                        output_messages.append(message)
                        
            elif event_name == "gen_ai.tool.message":
                # Tool messages - treat as user messages with tool role
                content = event_attrs.get('content', '')
                tool_id = event_attrs.get('id', '')
                if content:
                    message = self._parse_message_content(content, 'tool')
                    if message and tool_id:
                        message['message.tool_call_id'] = tool_id
                        input_messages.append(message)
        
        return input_messages, output_messages

    def _extract_messages_from_attributes(self, prompt: Any, completion: Any) -> Tuple[List[Dict], List[Dict]]:
        """Fallback method to extract messages from attributes."""
        input_messages = []
        output_messages = []
        
        if prompt:
            if isinstance(prompt, str):
                try:
                    prompt_data = json.loads(prompt)
                    if isinstance(prompt_data, list):
                        for msg in prompt_data:
                            normalized = self._normalize_message(msg)
                            if normalized.get('message.role') == 'user':
                                input_messages.append(normalized)
                except json.JSONDecodeError:
                    # Simple string prompt
                    input_messages.append({
                        'message.role': 'user',
                        'message.content': str(prompt)
                    })
        
        if completion:
            if isinstance(completion, str):
                try:
                    completion_data = json.loads(completion)
                    if isinstance(completion_data, list):
                        # Handle Strands completion format
                        message = self._parse_strands_completion(completion_data)
                        if message:
                            output_messages.append(message)
                except json.JSONDecodeError:
                    # Simple string completion
                    output_messages.append({
                        'message.role': 'assistant',
                        'message.content': str(completion)
                    })
        
        return input_messages, output_messages

    def _parse_message_content(self, content: str, role: str) -> Optional[Dict]:
        """Parse message content from Strands event format with enhanced JSON parsing."""
        if not content:
            return None
            
        try:
            # Try to parse as JSON first
            content_data = json.loads(content) if isinstance(content, str) else content
            
            if isinstance(content_data, list):
                # New Strands format: [{"text": "..."}, {"toolUse": {...}}, {"toolResult": {...}}]
                message = {
                    'message.role': role,
                    'message.content': '',
                    'message.tool_calls': []
                }
                
                text_parts = []
                for item in content_data:
                    if isinstance(item, dict):
                        if 'text' in item:
                            text_parts.append(str(item['text']))
                        elif 'toolUse' in item:
                            tool_use = item['toolUse']
                            tool_call = {
                                'tool_call.id': tool_use.get('toolUseId', ''),
                                'tool_call.function.name': tool_use.get('name', ''),
                                'tool_call.function.arguments': json.dumps(tool_use.get('input', {}))
                            }
                            message['message.tool_calls'].append(tool_call)
                        elif 'toolResult' in item:
                            # Handle tool results - extract text content
                            tool_result = item['toolResult']
                            if 'content' in tool_result:
                                if isinstance(tool_result['content'], list):
                                    for tr_content in tool_result['content']:
                                        if isinstance(tr_content, dict) and 'text' in tr_content:
                                            text_parts.append(str(tr_content['text']))
                                elif isinstance(tool_result['content'], str):
                                    text_parts.append(tool_result['content'])
                            # Set role to tool for tool results and include tool call ID
                            message['message.role'] = 'tool'
                            if 'toolUseId' in tool_result:
                                message['message.tool_call_id'] = tool_result['toolUseId']
                
                message['message.content'] = ' '.join(text_parts) if text_parts else ''
                
                # Clean up empty tool_calls
                if not message['message.tool_calls']:
                    del message['message.tool_calls']
                
                return message
            elif isinstance(content_data, dict):
                # Handle single dict format (like tool messages)
                if 'text' in content_data:
                    return {
                        'message.role': role,
                        'message.content': str(content_data['text'])
                    }
                else:
                    return {
                        'message.role': role,
                        'message.content': str(content_data)
                    }
            else:
                # Simple string content
                return {
                    'message.role': role,
                    'message.content': str(content_data)
                }
                
        except (json.JSONDecodeError, TypeError):
            # Fallback to string content
            return {
                'message.role': role,
                'message.content': str(content)
            }

    def _parse_strands_completion(self, completion_data: List[Any]) -> Optional[Dict]:
        """Parse Strands completion format into a message."""
        message = {
            'message.role': 'assistant',
            'message.content': '',
            'message.tool_calls': []
        }
        
        text_parts = []
        for item in completion_data:
            if isinstance(item, dict):
                if 'text' in item:
                    text_parts.append(str(item['text']))
                elif 'toolUse' in item:
                    tool_use = item['toolUse']
                    tool_call = {
                        'tool_call.id': tool_use.get('toolUseId', ''),
                        'tool_call.function.name': tool_use.get('name', ''),
                        'tool_call.function.arguments': json.dumps(tool_use.get('input', {}))
                    }
                    message['message.tool_calls'].append(tool_call)
        
        message['message.content'] = ' '.join(text_parts) if text_parts else ''
        
        # Clean up empty arrays
        if not message['message.tool_calls']:
            del message['message.tool_calls']
        
        return message if message['message.content'] or 'message.tool_calls' in message else None

    def _flatten_messages(self, messages: List[Dict], key_prefix: str, result: Dict[str, Any]):
        """Flatten message structure for OpenInference."""
        for idx, msg in enumerate(messages):
            for key, value in msg.items():
                clean_key = key.replace("message.", "") if key.startswith("message.") else key
                dotted_key = f"{key_prefix}.{idx}.message.{clean_key}"
                
                if clean_key == "tool_calls" and isinstance(value, list):
                    # Handle tool calls
                    for tool_idx, tool_call in enumerate(value):
                        if isinstance(tool_call, dict):
                            for tool_key, tool_val in tool_call.items():
                                tool_dotted_key = f"{key_prefix}.{idx}.message.tool_calls.{tool_idx}.{tool_key}"
                                result[tool_dotted_key] = self._serialize_value(tool_val)
                else:
                    result[dotted_key] = self._serialize_value(value)

    def _create_input_output_values(self, attrs: Dict[str, Any], result: Dict[str, Any],
                                   input_messages: List[Dict], output_messages: List[Dict]):
        """Create input.value and output.value for Arize compatibility."""
        span_kind = result.get("openinference.span.kind")
        model_name = result.get("llm.model_name") or attrs.get("gen_ai.request.model") or "unknown"
        
        if span_kind in ["LLM", "AGENT", "CHAIN"]:
            # Create input.value
            if input_messages:
                if len(input_messages) == 1 and input_messages[0].get('message.role') == 'user':
                    # Simple user message
                    result["input.value"] = input_messages[0].get('message.content', '')
                    result["input.mime_type"] = "text/plain"
                else:
                    # Complex conversation
                    input_structure = {
                        "messages": input_messages,
                        "model": model_name
                    }
                    result["input.value"] = json.dumps(input_structure, separators=(",", ":"))
                    result["input.mime_type"] = "application/json"
            
            # Create output.value  
            if output_messages:
                last_message = output_messages[-1]
                content = last_message.get('message.content', '')
                
                if span_kind == "LLM":
                    # LLM format
                    output_structure = {
                        "choices": [{
                            "finish_reason": last_message.get('message.finish_reason', 'stop'),
                            "index": 0,
                            "message": {
                                "content": content,
                                "role": last_message.get('message.role', 'assistant')
                            }
                        }],
                        "model": model_name,
                        "usage": {
                            "completion_tokens": result.get("llm.token_count.completion"),
                            "prompt_tokens": result.get("llm.token_count.prompt"),
                            "total_tokens": result.get("llm.token_count.total")
                        }
                    }
                    result["output.value"] = json.dumps(output_structure, separators=(",", ":"))
                    result["output.mime_type"] = "application/json"
                else:
                    # Simple text output for AGENT/CHAIN
                    result["output.value"] = content
                    result["output.mime_type"] = "text/plain"

    def _handle_tags(self, attrs: Dict[str, Any], result: Dict[str, Any]):
        """Handle both Strands arize.tags and standard tag.tags formats."""
        tags = None
        
        # Check for Strands format first
        if "arize.tags" in attrs:
            tags = attrs["arize.tags"]
        elif "tag.tags" in attrs:
            tags = attrs["tag.tags"]
        
        if tags:
            if isinstance(tags, list):
                result["tag.tags"] = tags
            elif isinstance(tags, str):
                result["tag.tags"] = [tags]

    def _determine_span_kind(self, span: Span, attrs: Dict[str, Any]) -> str:
        """Determine the OpenInference span kind with updated naming conventions."""
        span_name = span.name
        
        # Handle new span naming conventions
        if span_name == "chat":
            return "LLM"
        elif span_name.startswith("execute_tool "):
            return "TOOL"
        elif span_name == "execute_event_loop_cycle":
            return "CHAIN"
        elif span_name.startswith("invoke_agent"):
            return "AGENT"
        # Legacy support for old naming
        elif "Model invoke" in span_name:
            return "LLM"
        elif span_name.startswith("Tool:"):
            return "TOOL"
        elif "Cycle" in span_name:
            return "CHAIN"
        elif attrs.get("gen_ai.agent.name") or attrs.get("agent.name"):
            return "AGENT"
        
        return "CHAIN"
    
    def _set_graph_node_attributes(self, span: Span, attrs: Dict[str, Any], result: Dict[str, Any]):
        """Set graph node attributes for Arize visualization using span names."""
        span_name = span.name
        span_kind = result["openinference.span.kind"]        
        
        # Simple graph node attributes without hierarchy tracking
        if span_kind == "AGENT":
            result["graph.node.id"] = span_name
        elif span_kind == "CHAIN":
            result["graph.node.id"] = span_name
            result["graph.node.parent_id"] = "strands_agent"
        elif span_kind == "LLM":
            result["graph.node.id"] = span_name
            result["graph.node.parent_id"] = "strands_agent"
        elif span_kind == "TOOL":
            result["graph.node.id"] = span_name
            result["graph.node.parent_id"] = "strands_agent"

    def _handle_tool_span(self, attrs: Dict[str, Any], result: Dict[str, Any], events: List = None):
        """Handle tool-specific attributes with enhanced event processing."""
        # Extract tool information
        tool_name = attrs.get("gen_ai.tool.name")
        tool_call_id = attrs.get("gen_ai.tool.call.id")
        tool_status = attrs.get("tool.status")
        
        if tool_name:
            result["tool.name"] = tool_name
            
        if tool_call_id:
            result["tool.call_id"] = tool_call_id
            
        if tool_status:
            result["tool.status"] = tool_status
        
        # Extract tool parameters and input/output from events if available
        if events:
            tool_parameters = None
            tool_output = None
            
            for event in events:
                event_name = getattr(event, 'name', '') if hasattr(event, 'name') else event.get('name', '')
                event_attrs = getattr(event, 'attributes', {}) if hasattr(event, 'attributes') else event.get('attributes', {})
                
                if event_name == "gen_ai.tool.message":
                    # Tool input - extract parameters for tool.parameters attribute
                    content = event_attrs.get('content', '')
                    if content:
                        try:
                            content_data = json.loads(content) if isinstance(content, str) else content
                            if isinstance(content_data, dict):
                                tool_parameters = content_data
                            else:
                                tool_parameters = {"input": str(content_data)}
                        except (json.JSONDecodeError, TypeError):
                            tool_parameters = {"input": str(content)}
                            
                elif event_name == "gen_ai.choice":
                    # Tool output
                    message = event_attrs.get('message', '')
                    if message:
                        try:
                            message_data = json.loads(message) if isinstance(message, str) else message
                            if isinstance(message_data, list):
                                text_parts = []
                                for item in message_data:
                                    if isinstance(item, dict) and 'text' in item:
                                        text_parts.append(item['text'])
                                tool_output = ' '.join(text_parts) if text_parts else str(message_data)
                            else:
                                tool_output = str(message_data)
                        except (json.JSONDecodeError, TypeError):
                            tool_output = str(message)
            
            # Set the crucial tool.parameters attribute as JSON string
            if tool_parameters:
                result["tool.parameters"] = json.dumps(tool_parameters, separators=(",", ":"))
                
                # Create input messages showing the tool call that triggered this tool execution
                if tool_name and tool_call_id:
                    input_messages = [{
                        'message.role': 'assistant',
                        'message.content': '',
                        'message.tool_calls': [{
                            'tool_call.id': tool_call_id,
                            'tool_call.function.name': tool_name,
                            'tool_call.function.arguments': json.dumps(tool_parameters, separators=(",", ":"))
                        }]
                    }]
                    
                    # Set the flattened input messages for proper display in Arize
                    result["llm.input_messages"] = json.dumps(input_messages, separators=(",", ":"))
                    self._flatten_messages(input_messages, "llm.input_messages", result)
                
                # Also set input.value for display purposes
                if isinstance(tool_parameters, dict):
                    if 'text' in tool_parameters:
                        result["input.value"] = tool_parameters['text']
                        result["input.mime_type"] = "text/plain"
                    else:
                        result["input.value"] = json.dumps(tool_parameters, separators=(",", ":"))
                        result["input.mime_type"] = "application/json"
                        
            if tool_output:
                result["output.value"] = tool_output
                result["output.mime_type"] = "text/plain"

    def _map_tools(self, tools_data: Any, result: Dict[str, Any]):
        """Map tools from Strands to OpenInference format."""
        if isinstance(tools_data, str):
            try:
                tools_data = json.loads(tools_data)
            except json.JSONDecodeError:
                return
        
        if not isinstance(tools_data, list):
            return
        
        # Handle tool names as strings (Strands format)
        for idx, tool in enumerate(tools_data):
            if isinstance(tool, str):
                # Simple tool name
                result[f"llm.tools.{idx}.tool.name"] = tool
                result[f"llm.tools.{idx}.tool.description"] = f"Tool: {tool}"
            elif isinstance(tool, dict):
                # Full tool definition
                result[f"llm.tools.{idx}.tool.name"] = tool.get("name", "")
                result[f"llm.tools.{idx}.tool.description"] = tool.get("description", "")
                if "parameters" in tool or "input_schema" in tool:
                    schema = tool.get("parameters") or tool.get("input_schema")
                    result[f"llm.tools.{idx}.tool.json_schema"] = json.dumps(schema)

    def _map_token_usage(self, attrs: Dict[str, Any], result: Dict[str, Any]):
        """Map token usage metrics."""
        token_mappings = [
            ("gen_ai.usage.prompt_tokens", "llm.token_count.prompt"),
            ("gen_ai.usage.input_tokens", "llm.token_count.prompt"),  # Alternative name
            ("gen_ai.usage.completion_tokens", "llm.token_count.completion"),
            ("gen_ai.usage.output_tokens", "llm.token_count.completion"),  # Alternative name
            ("gen_ai.usage.total_tokens", "llm.token_count.total"),
        ]
        
        for strands_key, openinf_key in token_mappings:
            if value := attrs.get(strands_key):
                result[openinf_key] = value

    def _map_invocation_parameters(self, attrs: Dict[str, Any], result: Dict[str, Any]):
        """Map invocation parameters."""
        params = {}
        param_mappings = {
            "max_tokens": "max_tokens",
            "temperature": "temperature", 
            "top_p": "top_p",
        }
        
        for key, param_key in param_mappings.items():
            if key in attrs:
                params[param_key] = attrs[key]
        
        if params:
            result["llm.invocation_parameters"] = json.dumps(params, separators=(",", ":"))

    def _normalize_message(self, msg: Any) -> Dict[str, Any]:
        """Normalize a single message to OpenInference format."""
        if not isinstance(msg, dict):
            return {"message.role": "user", "message.content": str(msg)}
        
        result = {}
        if "role" in msg:
            result["message.role"] = msg["role"]
        
        # Handle content
        if "content" in msg:
            content = msg["content"]
            if isinstance(content, list):
                # Extract text from content array
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        text_parts.append(str(item["text"]))
                result["message.content"] = " ".join(text_parts) if text_parts else ""
            else:
                result["message.content"] = str(content)
        
        return result

    def _convert_to_nested_llm_format(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert flat LLM attributes to nested structure for Arize UI compatibility.
        
        Converts from flat format:
          llm.input_messages, llm.prompt_template.template, llm.token_count.completion
        
        To nested format:
          llm: { input_messages: [...], prompt_template: {...}, token_count: {...} }
        """
        # Extract all llm.* attributes
        llm_attrs = {}
        llm_keys_to_remove = []
        
        for key, value in result.items():
            if key.startswith('llm.'):
                # Convert flat key to nested structure
                nested_key = key[4:]  # Remove 'llm.' prefix
                llm_attrs[nested_key] = value
                llm_keys_to_remove.append(key)
        
        # Only proceed if we have LLM attributes
        if not llm_attrs:
            return result
        
        # Create nested LLM object
        llm_obj = {}
        
        # 1. Handle input_messages - add system prompt as first message
        if 'input_messages' in llm_attrs:
            try:
                input_messages = json.loads(llm_attrs['input_messages']) if isinstance(llm_attrs['input_messages'], str) else llm_attrs['input_messages']
                
                # Check if system prompt exists and add as first message if not already present
                system_prompt = None
                if 'prompt_template.template' in llm_attrs:
                    system_prompt = llm_attrs['prompt_template.template']
                
                # Check if first message is already system message
                has_system_message = (input_messages and 
                                    isinstance(input_messages, list) and 
                                    len(input_messages) > 0 and 
                                    input_messages[0].get('message.role') == 'system')
                
                # Add system message if we have system prompt and no existing system message
                if system_prompt and not has_system_message and system_prompt != "[System prompt not available - check AGENT span configuration]":
                    system_message = {
                        "message.content": system_prompt,
                        "message.role": "system"
                    }
                    input_messages = [system_message] + (input_messages if input_messages else [])
                
                llm_obj['input_messages'] = input_messages
            except (json.JSONDecodeError, TypeError):
                llm_obj['input_messages'] = llm_attrs['input_messages']
        
        # 2. Handle output_messages
        if 'output_messages' in llm_attrs:
            try:
                output_messages = json.loads(llm_attrs['output_messages']) if isinstance(llm_attrs['output_messages'], str) else llm_attrs['output_messages']
                llm_obj['output_messages'] = output_messages
            except (json.JSONDecodeError, TypeError):
                llm_obj['output_messages'] = llm_attrs['output_messages']
        
        # 3. Handle prompt_template as nested object
        if 'prompt_template.template' in llm_attrs:
            llm_obj['prompt_template'] = {
                'template': llm_attrs['prompt_template.template']
            }
            # Add variables if they exist
            if 'prompt_template.variables' in llm_attrs:
                llm_obj['prompt_template']['variables'] = llm_attrs['prompt_template.variables']
        
        # 4. Handle token_count as nested object
        token_count = {}
        if 'token_count.prompt' in llm_attrs:
            try:
                token_count['prompt'] = int(llm_attrs['token_count.prompt'])
            except (ValueError, TypeError):
                token_count['prompt'] = llm_attrs['token_count.prompt']
        if 'token_count.completion' in llm_attrs:
            try:
                token_count['completion'] = int(llm_attrs['token_count.completion'])  
            except (ValueError, TypeError):
                token_count['completion'] = llm_attrs['token_count.completion']
        if 'token_count.total' in llm_attrs:
            try:
                token_count['total'] = int(llm_attrs['token_count.total'])
            except (ValueError, TypeError):
                token_count['total'] = llm_attrs['token_count.total']
        
        if token_count:
            llm_obj['token_count'] = token_count
        
        # 5. Handle other simple attributes
        simple_attrs = ['model_name', 'system', 'provider', 'invocation_parameters']
        for attr in simple_attrs:
            if attr in llm_attrs:
                llm_obj[attr] = llm_attrs[attr]
        
        # 6. Handle nested attributes that don't need restructuring
        for key, value in llm_attrs.items():
            # Skip attributes we've already handled
            if key not in ['input_messages', 'output_messages', 'prompt_template.template', 'prompt_template.variables'] and not key.startswith('token_count.') and key not in simple_attrs:
                # For nested keys like "input_messages.0.message.content", keep them flat
                if '.' in key and not key.startswith('prompt_template') and not key.startswith('token_count'):
                    continue
                llm_obj[key] = value
        
        # Remove flat LLM attributes from result
        for key in llm_keys_to_remove:
            result.pop(key, None)
        
        # Add nested LLM object
        if llm_obj:
            result['llm'] = llm_obj
            self._debug_log('INFO', f'Converted to nested LLM format', 
                           nested_keys=list(llm_obj.keys()))
        
        return result

    def _add_arize_compatible_event(self, span: Span, input_messages: List[Dict], 
                                   output_messages: List[Dict], system_prompt: str, 
                                   attrs: Dict[str, Any]):
        """
        Add nested LLM data as span event for Arize UI compatibility (v2.7.0).
        
        Since OpenTelemetry span attributes must be flat, but Arize UI expects nested 
        'llm' object structure, we add an event with the nested format that Arize can process.
        """
        try:
            # Build nested LLM object matching Arize expectations
            llm_data = {}
            
            # 1. Input messages with system prompt first
            if input_messages:
                llm_data['input_messages'] = input_messages
            
            # 2. Output messages
            if output_messages:
                llm_data['output_messages'] = output_messages
            
            # 3. Prompt template as nested object
            llm_data['prompt_template'] = {
                'template': f'system: {system_prompt}'
            }
            
            # 4. Token count as nested object
            token_count = {}
            if prompt_tokens := attrs.get('gen_ai.usage.prompt_tokens'):
                try:
                    token_count['prompt'] = int(prompt_tokens)
                except (ValueError, TypeError):
                    token_count['prompt'] = str(prompt_tokens)
                    
            if completion_tokens := attrs.get('gen_ai.usage.completion_tokens'):
                try:
                    token_count['completion'] = int(completion_tokens)
                except (ValueError, TypeError):
                    token_count['completion'] = str(completion_tokens)
                    
            if total_tokens := attrs.get('gen_ai.usage.total_tokens'):
                try:
                    token_count['total'] = int(total_tokens)
                except (ValueError, TypeError):
                    token_count['total'] = str(total_tokens)
            
            if token_count:
                llm_data['token_count'] = token_count
            
            # 5. Model name
            if model_name := attrs.get('gen_ai.request.model'):
                llm_data['model_name'] = model_name
            
            # 6. Invocation parameters (if any)
            # This would need to be extracted from attributes if available
            
            # Create the event with nested structure
            event_data = {
                'llm': llm_data,
                'openinference': {
                    'span': {
                        'kind': 'LLM'
                    }
                }
            }
            
            # Add as span event - OpenTelemetry allows more complex data in events
            # Note: We serialize to JSON string since even events have some limitations
            span.add_event(
                name="arize.llm_data", 
                attributes={
                    'llm_nested_data': json.dumps(event_data, separators=(",", ":"))
                }
            )
            
            self._debug_log('INFO', 'Added Arize-compatible nested LLM event',
                           input_messages_count=len(input_messages) if input_messages else 0,
                           output_messages_count=len(output_messages) if output_messages else 0,
                           has_system_prompt=bool(system_prompt))
                           
        except Exception as e:
            self._debug_log('ERROR', f'Failed to add Arize-compatible event: {str(e)}')

    def _add_nested_llm_json_attribute(self, result: Dict[str, Any], input_messages: List[Dict], 
                                      output_messages: List[Dict], system_prompt: str, 
                                      attrs: Dict[str, Any]):
        """
        Add nested LLM data as JSON string attribute for Arize processing (v2.8.0).
        
        This tries multiple approaches to get Arize to recognize the nested format:
        1. Special 'llm' attribute with JSON string
        2. Special 'openinference.llm' attribute  
        3. Multiple attribute variations
        """
        try:
            # Build the nested LLM object exactly like the working example
            llm_nested = {
                "input_messages": input_messages,
                "output_messages": output_messages,
                "prompt_template": {
                    "template": f"system: {system_prompt}"
                },
                "model_name": attrs.get('gen_ai.request.model', '')
            }
            
            # Add token_count as nested object
            token_count = {}
            if prompt_tokens := attrs.get('gen_ai.usage.prompt_tokens'):
                try:
                    token_count['prompt'] = int(prompt_tokens)
                except (ValueError, TypeError):
                    token_count['prompt'] = str(prompt_tokens)
                    
            if completion_tokens := attrs.get('gen_ai.usage.completion_tokens'):
                try:
                    token_count['completion'] = int(completion_tokens)
                except (ValueError, TypeError):
                    token_count['completion'] = str(completion_tokens)
                    
            if total_tokens := attrs.get('gen_ai.usage.total_tokens'):
                try:
                    token_count['total'] = int(total_tokens)
                except (ValueError, TypeError):
                    token_count['total'] = str(total_tokens)
            
            if token_count:
                llm_nested['token_count'] = token_count
            
            # Convert to JSON string
            llm_json = json.dumps(llm_nested, separators=(",", ":"))
            
            # Try multiple attribute keys that Arize might recognize
            # Strategy 1: Direct 'llm' attribute (most likely)
            result['llm'] = llm_json
            
            # Strategy 2: OpenInference namespace
            result['openinference.llm'] = llm_json
            
            # Strategy 3: Arize-specific namespace  
            result['arize.llm_data'] = llm_json
            
            # Strategy 4: Full nested structure as string
            full_nested = {
                "llm": llm_nested,
                "openinference": {
                    "span": {
                        "kind": "LLM"
                    }
                }
            }
            result['arize.full_nested'] = json.dumps(full_nested, separators=(",", ":"))
            
            self._debug_log('INFO', 'Added nested LLM data as JSON attributes',
                           strategies=4, llm_json_length=len(llm_json))
                           
        except Exception as e:
            self._debug_log('ERROR', f'Failed to add nested LLM JSON attribute: {str(e)}')

    def _add_metadata(self, attrs: Dict[str, Any], result: Dict[str, Any]):
        """Add remaining attributes to metadata."""
        metadata = {}
        skip_keys = {"gen_ai.prompt", "gen_ai.completion", "gen_ai.agent.tools", "agent.tools", "system_prompt", "inherited_system_prompt"}
        
        for key, value in attrs.items():
            if key not in skip_keys and key not in result:
                metadata[key] = self._serialize_value(value)
        
        if metadata:
            result["metadata"] = json.dumps(metadata, separators=(",", ":"))

    def _filter_arize_attributes(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter out attributes with 'arize' parent and 'openinference.llm' from LLM spans.
        
        Removes:
        - arize.llm_data
        - arize.full_nested  
        - Any other arize.* attributes
        - openinference.llm
        
        Args:
            result: The attributes dictionary to filter
            
        Returns:
            Filtered attributes dictionary
        """
        filtered_result = {}
        
        for key, value in result.items():
            # Skip any attribute that starts with "arize."
            if key.startswith("arize."):
                self._debug_log('INFO', f'Filtering out arize attribute from LLM span', 
                               attribute=key)
                continue
            # Skip openinference.llm attribute
            elif key == "openinference.llm":
                self._debug_log('INFO', f'Filtering out openinference.llm attribute from LLM span')
                continue
            # Keep all other attributes
            filtered_result[key] = value
            
        return filtered_result

    def _serialize_value(self, value: Any) -> Any:
        """Ensure a value is serializable."""
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        
        try:
            return json.dumps(value, separators=(",", ":"))
        except (TypeError, OverflowError):
            return str(value)

    def shutdown(self):
        """Called when the processor is shutdown."""
        self._debug_log('INFO', f'Processor shutting down', 
                       processed_spans=len(self.processed_spans))

    def force_flush(self, timeout_millis=None):
        """Called to force flush."""
        return True

    def get_processor_info(self) -> Dict[str, Any]:
        """
        Returns information about the processor's capabilities and status.
        
        Returns:
            Dict containing processor information and diagnostic data.
        """
        return {
            "processor_name": "StrandsToOpenInferenceProcessor",
            "version": "2.8.3-simplified",
            "supports_events": True,
            "supports_deprecated_attributes": True,
            "supports_new_semantic_conventions": True,
            "supports_environment_variable_system_prompt": True,
            "processed_spans": len(self.processed_spans),
            "debug_enabled": self.debug,
            "last_prompt_source": self.last_prompt_source,
            "supported_span_kinds": ["LLM", "AGENT", "CHAIN", "TOOL"],
            "supported_span_names": [
                "chat", "execute_event_loop_cycle", "execute_tool [name]", 
                "invoke_agent [name]", "Model invoke", "Cycle [UUID]", "Tool: [name]"
            ],
            "supported_event_types": [
                "gen_ai.user.message", "gen_ai.assistant.message", 
                "gen_ai.choice", "gen_ai.tool.message", "gen_ai.system.message"
            ],
            "system_prompt_strategies": [
                "environment_variable (STRANDS_AGENT_SYSTEM_PROMPT only)"
            ],
            "features": [
                "Environment variable system prompt support",
                "Robust span ID normalization",
                "Comprehensive debug logging",
                "Event-based message extraction",
                "Enhanced JSON content parsing",
                "Tool result processing",
                "Updated span naming conventions",
                "OpenInference semantic convention compliance",
                "Strands-specific format parsing",
                "Graph node hierarchy mapping",
                "Token usage tracking",
                "Tool call processing",
                "Multi-format content support"
            ]
        }