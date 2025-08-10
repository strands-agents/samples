"""
Integrates with to NVIDIA NeMO server running locally.
"""
from strands.hooks import HookProvider, HookRegistry, MessageAddedEvent
from typing import Dict
import httpx

class CustomGuardrailHook(HookProvider):
    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(MessageAddedEvent, self.guardrail_check)        

    def guardrail_check(self, event: MessageAddedEvent) -> None:
        """
        This is the main guardrail check that will be called when a message is added to the agent's conversation.
        Processes messages in AWS Bedrock Message format.
        Checks both user and assistant messages.
        """
        try:
            # Extract text content and role from AWS Bedrock Message format
            message_text, role = extract_text_and_role_from_bedrock_message(event.agent.messages[-1])
            
            # If extraction fails, use string representation as fallback
            if message_text is None:
                message_text = str(event.agent.messages[-1])
            
                
            payload = {
                "config_id": "my-first-guardrail",
                "messages": [{
                    "role": role,
                    "content": message_text
                }]
            }

            headers = {
                "Content-Type": "application/json"
            }
            
            url = "http://127.0.0.1:8000/v1/chat/completions"
            
            try:
                response = httpx.post(url, headers=headers, json=payload, timeout=10.0)
                response.raise_for_status()
                
                response_data = response.json()
                messages = response_data.get("messages")
                
                if not messages or not isinstance(messages, list) or len(messages) == 0:
                    raise Exception("Guardrail check failed: No messages returned from guardrail service")
                
                guardrail_response = messages[0].get("content")
                
                # Accept "ALLOW" or empty string as allowed responses
                if guardrail_response not in ["ALLOW", ""]:
                    raise Exception(f"Guardrail check failed: Content not allowed - Message: '{message_text}' (got: '{guardrail_response}')")
                    
                print("Guardrail check passed, proceeding with request.")
                
            except httpx.TimeoutException:
                print("Warning: Guardrail service timeout, allowing request to proceed")
            except httpx.ConnectError:
                print("Warning: Cannot connect to guardrail service, allowing request to proceed")
            except httpx.HTTPStatusError as e:
                raise Exception(f"Guardrail check failed with HTTP status {e.response.status_code}")
            except Exception as e:
                if "Guardrail check failed" in str(e):
                    raise
                print(f"Warning: Guardrail check error ({e}), allowing request to proceed")
                
        except Exception as e:
            if "Guardrail check failed" in str(e):
                raise
            print(f"Error in guardrail check: {e}")
            print("Allowing request to proceed due to guardrail error")


def extract_text_and_role_from_bedrock_message(message: Dict):
    """
    Extract text content and role from AWS Bedrock Message format.
    
    AWS Bedrock Message format:
    {
        "role": "user" | "assistant",
        "content": [
            {
                "text": "string content"
            }
        ]
    }
    
    Returns:
        tuple: (text_content, role) or (None, "user") if extraction fails
    """
    try:
        # Check if message follows AWS Bedrock Message format
        if 'content' in message and isinstance(message['content'], list) and message['content']:
            # Extract text from all content blocks
            text_parts = []
            for content_block in message['content']:
                if 'text' in content_block:
                    text_parts.append(content_block['text'])
            
            # Join all text parts if multiple content blocks exist
            text_content = ' '.join(text_parts) if text_parts else None
            
            # Extract role, default to "user" if not found
            role = message.get('role', 'user')
            
            return text_content, role

        # Fallback: if it's already a string, return as-is with default role
        elif isinstance(message, str):
            return message, 'user'
            
        # Return None if the expected structure is not found
        return None, 'user'

    except (KeyError, IndexError, TypeError) as e:
        # Handle potential errors like missing keys or wrong types
        print(f"An error occurred extracting text from message: {e}")
        return None, 'user'