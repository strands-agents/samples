"""
EXAMPLE ONLY
Defines a custom hook for plugging into third-party guardrails tools.

Blocks toxic language from the hub://guardrails/toxic_language guardrail
"""
from strands.hooks import HookProvider, HookRegistry, MessageAddedEvent
from typing import Dict, Any

from guardrails.hub import ToxicLanguage
from guardrails import Guard


class CustomGuardrailHook(HookProvider):
    def __init__(self):
        self.guard = Guard().use_many(
            ToxicLanguage(on_fail="exception")
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
                # Extract text from tool results
                tool_result = block['toolResult']
                if 'content' in tool_result:
                    for content in tool_result['content']:
                        if 'text' in content:
                            text_parts.append(content['text'])
        
        return ' '.join(text_parts)

    def guardrail_check(self, event):
        # Get the latest message from the event
        latest_message = event.agent.messages[-1]
        
        if latest_message.get('role') == 'user':
            # Extract text content from the Bedrock Message format
            message_text = self.extract_text_from_message(latest_message)
            
            if message_text.strip():
                try:
                    # Run Guardrails AI validation on the extracted text
                    result = self.guard.validate(message_text)
                    
                    # Log the validation result
                    if result.validation_passed:
                        print(f"✓ User message passed all guardrail checks")
                    else:
                        print(f"✗ User message failed guardrail checks - BLOCKING MESSAGE")
                        # Block the message by raising an exception to prevent LLM processing
                        raise ValueError(f"Message blocked due to policy violations: {result.validation_summaries}")
                        
                except Exception as e:
                    print(f"🚫 BLOCKING MESSAGE: {e}")
                    # Re-raise to prevent further processing
                    raise e
            else:
                print("No text content found in user message to validate")
        else:
            print(f"✓ Assistant response processed normally")
