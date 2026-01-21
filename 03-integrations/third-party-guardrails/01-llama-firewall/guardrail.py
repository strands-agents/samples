"""
EXAMPLE ONLY
Defines a custom hook for plugging into third-party guardrails tools.

The PII_DETECTION and AGENT_ALIGNMENT scanners require a `TOGETHER_API_KEY` so have been excluded from this example.

Valid roles are `user` and `assistant`.
https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Message.html
"""
from strands.hooks import HookProvider, HookRegistry, MessageAddedEvent
from typing import Dict,Any
import asyncio
from llamafirewall import LlamaFirewall, UserMessage, AssistantMessage, Role, ScannerType


class CustomGuardrailHook(HookProvider):
    def __init__(self):
             
        # Configure LlamaFirewall with multiple scanners for comprehensive protection
        self.firewall = LlamaFirewall(
            scanners={
                Role.USER: [
                    ScannerType.PROMPT_GUARD,
                    ScannerType.REGEX,
                    ScannerType.CODE_SHIELD,
                    ScannerType.HIDDEN_ASCII

                ],
                Role.ASSISTANT: [
                    ScannerType.PROMPT_GUARD,
                    ScannerType.REGEX,
                    ScannerType.CODE_SHIELD,
                    ScannerType.HIDDEN_ASCII
                ],
            }
        )
    
    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(MessageAddedEvent, self.guardrail_check)        

    def extract_text_from_message(self, message: Dict[str, Any]) -> str:
        """Extract text content from a Bedrock Message object."""
        content_blocks = message.get('content', [])
        text_parts = []
        
        for block in content_blocks:
            if 'text' in block:
                text_parts.append(block['text'])
            elif 'toolResult' in block:
                tool_result = block['toolResult']
                if 'content' in tool_result:
                    for content in tool_result['content']:
                        if 'text' in content:
                            text_parts.append(content['text'])
        
        return ' '.join(text_parts)

    def check_with_llama_firewall(self, text: str, role: str) -> Dict[str, Any]:
        """Check text content using LlamaFirewall."""
        try:
            # Create appropriate message object based on role
            if role == 'user':
                message = UserMessage(content=text)
            elif role == 'assistant':
                message = AssistantMessage(content=text)
            else:
                # Default to user message for unknown roles
                message = UserMessage(content=text)
            
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create new event loop in thread if one is already running
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.firewall.scan_async(message))
                        result = future.result()
                else:
                    result = asyncio.run(self.firewall.scan_async(message))
            except AttributeError:
                # Fallback to sync method if async not available
                result = self.firewall.scan(message)

            decision_str = str(getattr(result, 'decision', 'ALLOW'))
            is_safe = 'ALLOW' in decision_str
            
            return {
                'safe': is_safe,
                'decision': getattr(result, 'decision', 'ALLOW'),
                'reason': getattr(result, 'reason', ''),
                'score': getattr(result, 'score', 0.0),
                'status': getattr(result, 'status', 'UNKNOWN'),
                'role': role
            }
        except Exception as e:
            print(f"LlamaFirewall check failed: {e}")
            # Fail secure - if guardrail check fails, treat as unsafe
            return {'safe': False, 'error': str(e), 'role': role, 'decision': 'BLOCK'}

    def guardrail_check(self, event: MessageAddedEvent) -> None:
        """
        Check the newest message from event.agent.messages array using Llama guardrails.
        Handles both input messages and responses according to Bedrock Message schema.
        """
        if not event.agent.messages:
            print("No messages in event.agent.messages")
            return

        # Get the newest message from the array
        newest_message = event.agent.messages[-1]
        
        # Extract role and text content according to Bedrock Message schema
        role = newest_message.get('role', 'unknown')
        text_content = self.extract_text_from_message(newest_message)
        
        if not text_content.strip():
            print(f"No text content found in {role} message")
            return
        
        print(f"Checking {role} message with LlamaFirewall...")
        print(f"Content preview: {text_content[:100]}...")
        
        # Run LlamaFirewall check
        guard_result = self.check_with_llama_firewall(text_content, role)
        
        if not guard_result.get('safe', True):
            print(f"🚨 GUARDRAIL VIOLATION DETECTED in {role} message:")
            print(f"  Decision: {guard_result.get('decision', 'BLOCK')}")
            print(f"  Reason: {guard_result.get('reason', 'Unknown')}")
            print(f"  Score: {guard_result.get('score', 0.0)}")
            print(f"  Status: {guard_result.get('status', 'UNKNOWN')}")
            
            # Block the message by raising an exception
            raise Exception(f"Message blocked by guardrail: {guard_result.get('reason', 'Security violation detected')}")
        else:
            print(f"✅ {role} message passed guardrail check")
            print(f"  Score: {guard_result.get('score', 0.0)}")
            print(f"  Status: {guard_result.get('status', 'SUCCESS')}")
            
        return guard_result