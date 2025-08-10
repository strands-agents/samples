"""
Defines a custom hook for plugging into thrird-party guardrails tools.
"""
from strands.hooks import HookProvider, HookRegistry, AfterInvocationEvent, MessageAddedEvent
from strands.experimental.hooks import BeforeModelInvocationEvent, AfterModelInvocationEvent
import json
from typing import Dict
import httpx

class CustomGuardrailHook(HookProvider):
    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(MessageAddedEvent, self.guardrail_check)        

        # registry.add_callback(BeforeModelInvocationEvent, self.check_input)        
        # registry.add_callback(AfterModelInvocationEvent, self.check_output)
        # registry.add_callback(AfterInvocationEvent, self.check_output)

    def check_input(self, event: BeforeModelInvocationEvent) -> None:
        """
        We need to check the input for alls calls to the LLM, not just user-provided calls
        """
        # just yeet the entire message into the guardrail.

        message = extract_text_from_json(event.agent.messages[-1])


        payload= {
            "config_id": "my-first-guardrail",
            "messages": [{
                "role":"user",
                "content": message
            }]
        }

        headers = {
            "Content-Type": "application/json"
        }
        

        url = "http://127.0.0.1:8000/v1/chat/completions"
        response = httpx.post(url, headers=headers, json=payload)

        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()

        if response.status_code != 200:
            raise Exception(f"Guardrail check failed with status code {response.status_code}")
    
        messages = response.json().get("messages")
        try:
            if messages[0].get("content") != "ALLOW":
                raise Exception("Guardrail check failed")

        except KeyError:
            raise Exception("Guardrail check failed: No messages returned from guardrail service")
        
        print("Guardrail check passed, proceeding with request.")


    def check_output(self, event: AfterInvocationEvent) -> None:
        # message = extract_text_from_json(event.agent.messages[-1])
        print("MESSAGE", event.agent.messages[-1])
        # print(message)

    def guardrail_check(self, event: MessageAddedEvent) -> None:
        """
        This is the main guardrail check that will be called when a message is added to the agent's conversation.

        I think you can just yeet the entire message into the guardrail, rather than add loads of processing on each message.
        """
        # message = extract_text_from_json(event.agent.messages[-1])
        # print("MESSAGE", message)
        payload= {
            "config_id": "akingscote-nemo-guardrail-example",
            "messages": [{
                "role":"user",
                "content": str(event.agent.messages[-1])
            }]
        }

        headers = {
            "Content-Type": "application/json"
        }
        

        url = "http://127.0.0.1:8000/v1/chat/completions"
        response = httpx.post(url, headers=headers, json=payload)

        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()

        if response.status_code != 200:
            raise Exception(f"Guardrail check failed with status code {response.status_code}")
    
        messages = response.json().get("messages")
        try:
            if messages[0].get("content") != "ALLOW":
                raise Exception("Guardrail check failed")

        except KeyError:
            raise Exception("Guardrail check failed: No messages returned from guardrail service")
        
        print("Guardrail check passed, proceeding with request.")


def extract_text_from_json(message: Dict):
    """
    """
    try:
        # Check if 'content' key exists and is a non-empty list
        if 'content' in message and message['content']:
            content_item = message['content'][0]

            # First, check for the 'toolResult' structure
            if 'toolResult' in content_item:
                # Navigate through the nested structure
                tool_content = content_item.get('toolResult', {}).get('content', [])
                if tool_content and 'text' in tool_content[0]:
                    return tool_content[0]['text']
            
            # If not, check for the direct 'text' key structure
            elif 'text' in content_item:
                return content_item['text']

        # Return None if the expected structure is not found
        return None

    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as e:
        # Handle potential errors like invalid JSON, missing keys, or wrong types
        print(f"An error occurred: {e}")
        return None