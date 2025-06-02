# Memory Persistent Agents

This tutorial demonstrates how to build Strands Agents that can remember information across multiple interactions by leveraging persistent memory.

## Key Concepts

- **Agent Memory**: Enables agents to store and recall information from previous conversations
- **Persistence**: Information remains available even after restarting the agent
- **Implementation**: Uses the `mem0_memory` tool from [mem0.ai](https://mem0.ai)

## Use Cases

- Personal assistants that remember user preferences
- Customer support bots that maintain conversation context
- Educational agents that track learning progress
- Any application where conversation history adds value

## Getting Started

### Option 1: Interactive Notebook
Run through the included Jupyter notebook to understand memory concepts and implementation with Strands agents.

### Option 2: Command Line Demo
For an interactive chat experience:

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Launch the agent:
   ```
   python personal_agent_with_memory.py
   ```

3. Interact with the agent by asking questions or providing information

## Experiment Ideas

- Tell the agent personal facts and verify recall in later conversations
- Test memory persistence by restarting the agent between interactions
- Compare with non-persistent agents to see the difference in user experience