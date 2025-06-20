from strands import Agent
from strands.models.anthropic import AnthropicModel
from kurrentdb_session_manager import KurrentDBConversationManager

"""
This is an example usage of the KurrentDBConversationManager with an Anthropic model.
"""

def main():
    unique_run_id = "run-01"
    kurrentdb_conversation_manager = (
        KurrentDBConversationManager(unique_run_id, "esdb://localhost:2113?Tls=false")
    )  # replace with your actual connection string

    # kurrentdb_conversation_manager.set_max_window_age(60) # Set max window age to 60 seconds
    model = AnthropicModel(
        client_args={
            "api_key": "Your API KEY here",  # Replace with your actual API key
        },
        # **model_config
        max_tokens=4096,
        model_id="claude-3-5-haiku-latest",
        params={
            "temperature": 0.7,
        }
    )

    poet_agent = Agent(
        system_prompt="You are a hungry poet who loves to write haikus about everything.",
        model=model,
        conversation_manager=kurrentdb_conversation_manager,  # Assuming no specific conversation manager is needed
    )
    poet_agent("Write a haiku about the beauty of nature.")
    kurrentdb_conversation_manager.save_agent_state(unique_run_id=unique_run_id,
                                                    state={"messages": poet_agent.messages,
                                                           "system_prompt": poet_agent.system_prompt})
    poet_agent("Based on the previous haiku, write another one about the changing seasons.")
    poet_agent = kurrentdb_conversation_manager.restore_agent_state(agent=poet_agent, unique_run_id=unique_run_id)
    poet_agent("What did we just talk about?")


if __name__ == "__main__":
    main()
