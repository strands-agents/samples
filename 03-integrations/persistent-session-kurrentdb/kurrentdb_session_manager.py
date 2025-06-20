from strands.agent.conversation_manager import ConversationManager
from strands.agent import Agent
from strands.types.content import Messages
from typing import Optional
from kurrentdbclient import KurrentDBClient, NewEvent, StreamState
from kurrentdbclient.exceptions import NotFoundError
import json

"""
Example usage:
from strands import Agent
from strands.models.anthropic import AnthropicModel
from kurrentdb_session_manager import KurrentDBConversationManager

unique_run_id = "run-01"
kurrentdb_conversation_manager = (
    KurrentDBConversationManager(unique_run_id, "esdb://localhost:2113?Tls=false")
) # replace with your actual connection string

# kurrentdb_conversation_manager.set_max_window_age(60) # Set max window age to 60 seconds
model = AnthropicModel(
        client_args={
            "api_key": "Your API KEY here",  # Replace with your actual API key
        },
        # **model_config
        max_tokens= 4096,
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
poet_agent = kurrentdb_conversation_manager.restore_agent_state(agent=poet_agent,unique_run_id=unique_run_id)
poet_agent("What did we just talk about?")
"""
class KurrentDBConversationManager(ConversationManager):
    client: KurrentDBClient
    def __init__(self, unique_run_id:str,
                 connection_string: str = "esdb://localhost:2113?Tls=false",
                 window_size: int = 40,
                 reducer_function = lambda x: x) -> None:
        """
        Initializes the KurrentDB conversation manager with a connection string.
        :param connection_string: The connection string for KurrentDB.
        """
        self.client = KurrentDBClient(connection_string)
        self.stream_id = unique_run_id
        self.checkpoint = -1  # Default checkpoint value, no messages processed yet
        self.window_size = window_size  # Maximum number of messages to keep in the conversation
        self.reducer_function = reducer_function  # Function to reduce messages if needed

    def apply_management(self, messages: Messages) -> None:
        """Apply management strategies to the messages list."""
        justRestored = False
        try:
            events = self.client.get_stream(
                stream_name=self.stream_id,
                resolve_links=True,
                backwards=True,
                limit=1
            )  # Get the last event in the stream
            if len(events) == 1 and events[0].type == "StateRestored":
                # then we don't need to remove any message
                justRestored = True
                self.checkpoint = events[0].stream_position

        except NotFoundError as e:
            #this means that the stream does not exist yet
            if self.checkpoint != -1:
                # Handle inconsistency in the outside the conversation manager
                raise Exception("Inconsistent state: Stream not found but checkpoint exists.")
        if self.checkpoint != -1 and justRestored == False:
            # remove already added messages from the messages list
            messages = messages[self.checkpoint + 1:]  # Keep only new messages
        events = []
        for message in messages:
            metadata = {}
            event = NewEvent(type=message["role"], data=bytes(json.dumps(message), 'utf-8'),
                             content_type='application/json',
                             metadata=bytes(json.dumps(metadata), 'utf-8'))
            events.append(event)
        self.client.append_to_stream(
            stream_name=self.stream_id,
            events=events,
            current_version=StreamState.ANY  # TODO: tighten this up if needed if agent is called in parallel and order is important(is that possible?)
        )
        self.checkpoint += len(events)  # Update checkpoint after appending messages


    def reduce_context(self, messages: Messages, e: Optional[Exception] = None) -> Optional[Messages]:
        """Function to reduce the context window size when it exceeds the model's limit.
        """
        return self.reducer_function(messages)

    def set_max_window_age(self, max_age: int) -> None:
        """Set the maximum age for messages in the conversation inside KurrentDB."""
        self.client.set_stream_metadata(self.stream_id,
                                        metadata={"$maxAge": max_age},
                                        current_version=StreamState.ANY
                                        )

    def set_max_window_size(self, max_count: int) -> None:
        """Set the maximum size for the conversation history inside KurrentDB."""
        self.client.set_stream_metadata(self.stream_id,
                                        metadata={"$maxCount": max_count},
                                        current_version=StreamState.ANY
                                        )

    def save_agent_state(self, unique_run_id: str, state: dict) -> None:
        """
        Saves the agent state variables to a checkpoint stream in KurrentDB.
        This event contains which position in the stream the agent is at and other state variables.
        """
        del state["messages"] # We already keep messages in the stream, so we don't need to save them again.
        state["kurrentdb_checkpoint"] = self.checkpoint
        state["kurrentdb_checkpoint_stream_id"] = unique_run_id
        event = NewEvent(type="agent_state", data=bytes(json.dumps(state), 'utf-8'),
                         content_type='application/json')
        self.client.append_to_stream(
            stream_name="strands_checkpoint-" + unique_run_id,
            events=[event],
            current_version=StreamState.ANY)


    def restore_agent_state(self, agent: Agent, unique_run_id: str) -> Agent:
        """
        Builds the agent state messages from a stream in KurrentDB.
        """
        try:
            checkpoint_event = self.client.get_stream(
                stream_name="strands_checkpoint-" + unique_run_id,
                resolve_links=True,
                backwards=True,
                limit=1
            )
            if not checkpoint_event or len(checkpoint_event) == 0:
                return None  # No state found

            state = json.loads(checkpoint_event[0].data.decode('utf-8'))
            self.stream_id = state["kurrentdb_checkpoint_stream_id"]
            self.checkpoint = state["kurrentdb_checkpoint"]

            messages = []
            message_events = self.client.get_stream(
                stream_name=unique_run_id,
                resolve_links=True,
                backwards=True,
                stream_position=self.checkpoint,
                limit=self.window_size
            )
            for event in message_events:
                if event.type == "StateRestored":
                    break #reached of this state
                message = json.loads(event.data.decode('utf-8'))
                messages.insert(0,message)
            state["messages"] = messages
            agent.messages = messages

            #append an event to know restore state was called
            system_event = NewEvent(
                type="StateRestored",
                data=bytes("{}", 'utf-8'),
                content_type='application/json',
                metadata=bytes("{}", 'utf-8')
            )
            self.client.append_to_stream(
            stream_name=unique_run_id,
            events=[system_event],
            current_version=StreamState.ANY
            )
            return agent
        except NotFoundError as e:
            return agent #unchanged agent, no state to restore
