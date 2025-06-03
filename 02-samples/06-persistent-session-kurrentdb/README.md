# KurrentDB Conversation Manager for Strands Agent

A persistent conversation manager implementation for Strands Agent that uses KurrentDB as the storage backend. This manager enables conversation history persistence, state management, and recovery capabilities for AI agents.

## Overview

The `KurrentDBConversationManager` extends the Strands framework's `ConversationManager` to provide:

- **Persistent Message Storage**: All conversation messages are stored as events in KurrentDB streams
- **State Checkpointing**: Save and restore agent state at any point in the conversation
- **Conversation History Management**: Configure retention policies with maximum age or count limits
- **Recovery Capabilities**: Restore agent state and conversation history after restarts

## Installation

### Prerequisites

- Python 3.7+
- KurrentDB instance running (default: `localhost:2113`)
- Required Python packages:
  ```bash
  pip install strands kurrentdbclient
  ```
## Quick Start
```json
pip install strands-agents[anthropic]
```
Setup an instance of KurrentDB: https://console.kurrent.cloud/signup or https://aws.amazon.com/marketplace/pp/prodview-kxo6grvoovk2y?sr=0-1&ref_=beagle&applicationId=AWSMPContessa
```python
from strands import Agent
from strands.models.anthropic import AnthropicModel
from kurrentdb_session_manager import KurrentDBConversationManager

unique_run_id = "run-01"
kurrentdb_conversation_manager = (
    KurrentDBConversationManager(unique_run_id, "connection string here")
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




```

## Features

### 1. Persistent Message Storage

Every message in the conversation is automatically stored as an event in KurrentDB:
- Each message is stored with its role (user/assistant/system) as the event type
- Messages are stored in order with stream positions for accurate replay

### 2. State Management

Save and restore complete agent state:

```python
# Save current state
conversation_manager.save_agent_state(
    unique_run_id="run-01",
    state={
        "messages": agent.messages,
        "system_prompt": agent.system_prompt,
        "custom_data": "any additional state"
    }
)

# Restore state later
agent = conversation_manager.restore_agent_state(
    agent=agent,
    unique_run_id="run-01"
)
```

### 3. Conversation Retention Policies

Configure how long conversations are retained:

```python
# Set maximum age (in seconds)
conversation_manager.set_max_window_age(3600)  # Keep messages for 1 hour

# Set maximum message count
conversation_manager.set_max_window_size(100)  # Keep last 100 messages
```

### 4. Window Size Management

Control how many messages are loaded into memory:

```python
conversation_manager = KurrentDBConversationManager(
    unique_run_id="run-01",
    connection_string="esdb://localhost:2113?Tls=false",
    window_size=40  # Load last 40 messages by default
)
```

## API Reference

### Constructor

```python
KurrentDBConversationManager(
    unique_run_id: str,
    connection_string: str = "esdb://localhost:2113?Tls=false",
    window_size: int = 40,
    reducer_function = lambda x: x
)
```

**Parameters:**
- `unique_run_id`: Unique identifier for the conversation stream
- `connection_string`: KurrentDB connection string
- `window_size`: Maximum number of messages to keep in memory
- `reducer_function`: Function to reduce messages if context limit is exceeded

### Methods

#### `apply_management(messages: Messages) -> None`
Applies management strategies to the messages list and persists new messages to KurrentDB.

#### `reduce_context(messages: Messages, e: Optional[Exception] = None) -> Optional[Messages]`
Reduces the context window size when it exceeds limits using the configured reducer function.

#### `set_max_window_age(max_age: int) -> None`
Sets the maximum age for messages in the conversation (KurrentDB stream metadata).

#### `set_max_window_size(max_count: int) -> None`
Sets the maximum number of messages to retain in the stream.

#### `save_agent_state(unique_run_id: str, state: dict) -> None`
Saves the current agent state to a checkpoint stream.

#### `restore_agent_state(agent: Agent, unique_run_id: str) -> Agent`
Restores agent state from the checkpoint stream.

## How It Works

### Stream Structure

The manager uses two types of streams in KurrentDB:

1. **Conversation Stream** (`{unique_run_id}`):
   - Contains all conversation messages as events
   - Event types: "user", "assistant", "system", "StateRestored"
   - Messages stored in chronological order

2. **Checkpoint Stream** (`strands_checkpoint-{unique_run_id}`):
   - Contains agent state snapshots
   - Used for recovery and state restoration
