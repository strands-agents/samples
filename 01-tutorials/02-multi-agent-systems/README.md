# Multi-Agent Systems

This tutorial section explores different approaches to building multi-agent systems using Strands Agents SDK.

## Approaches to Multi-Agent Systems

### 1. Agents as Tools 
[Link to docs](https://strandsagents.com/latest/user-guide/concepts/multi-agent/agents-as-tools/)

The "Agents as Tools" pattern creates a hierarchical structure where specialized AI agents are wrapped as callable functions (tools) that can be used by other agents:

- **Orchestrator Agent**: Handles user interaction and delegates tasks to specialized agents
- **Specialized Tool Agents**: Perform domain-specific tasks when called by the orchestrator
- **Key Benefits**: Separation of concerns, hierarchical delegation, modular architecture

Implementation involves using the `@tool` decorator to transform specialized agents into callable functions:

```python
@tool
def research_assistant(query: str) -> str:
    """Process and respond to research-related queries."""
    research_agent = Agent(system_prompt=RESEARCH_ASSISTANT_PROMPT)
    return str(research_agent(query))
```


### 2. Agent Swarms
[Link to docs](https://strandsagents.com/latest/user-guide/concepts/multi-agent/swarm/)

Agent swarms leverage collective intelligence through a collection of autonomous AI agents working together:

- **Decentralized Control**: No single agent directs the entire system
- **Shared Memory**: Agents exchange insights to build collective knowledge
- **Coordination Mechanisms**: Collaborative, competitive, or hybrid approaches
- **Communication Patterns**: Mesh networks where agents can communicate with each other

The built-in `swarm` tool simplifies implementation:

```python
from strands import Agent
from strands_tools import swarm

agent = Agent(tools=[swarm])
result = agent.tool.swarm(
    task="Analyze this dataset and identify market trends",
    swarm_size=4,
    coordination_pattern="collaborative"
)
```

### 3. Agent Graphs
[Link to docs](https://strandsagents.com/latest/user-guide/concepts/multi-agent/graph/)

Agent graphs provide structured networks of interconnected AI agents with explicit communication pathways:

- **Nodes (Agents)**: Individual AI agents with specialized roles
- **Edges (Connections)**: Define communication pathways between agents
- **Topology Patterns**: Star, mesh, or hierarchical structures

The `agent_graph` tool enables creation of sophisticated agent networks:

```python
from strands import Agent
from strands_tools import agent_graph

agent = Agent(tools=[agent_graph])
agent.tool.agent_graph(
    action="create",
    graph_id="research_team",
    topology={
        "type": "star",
        "nodes": [
            {"id": "coordinator", "role": "team_lead"},
            {"id": "data_analyst", "role": "analyst"},
            {"id": "domain_expert", "role": "expert"}
        ],
        "edges": [
            {"from": "coordinator", "to": "data_analyst"},
            {"from": "coordinator", "to": "domain_expert"}
        ]
    }
)
```

### 4. Agent Workflows
[Link to docs](https://strandsagents.com/latest/user-guide/concepts/multi-agent/workflow/)

Agent workflows coordinate tasks across multiple AI agents in defined sequences with clear dependencies:

- **Task Definition**: Clear description of what each agent needs to accomplish
- **Dependency Management**: Sequential dependencies, parallel execution, join points
- **Information Flow**: Connecting one agent's output to another's input

The `workflow` tool handles task creation, dependency resolution, and execution:

```python
from strands import Agent
from strands_tools import workflow

agent = Agent(tools=[workflow])
agent.tool.workflow(
    action="create",
    workflow_id="data_analysis",
    tasks=[
        {
            "task_id": "data_extraction",
            "description": "Extract key data from the report"
        },
        {
            "task_id": "analysis",
            "description": "Analyze the extracted data",
            "dependencies": ["data_extraction"]
        }
    ]
)
```

## Choosing the Right Approach

- **Agents as Tools**: Best for clear hierarchical structures with specialized expertise
- **Agent Swarms**: Ideal for collaborative problem-solving with emergent intelligence
- **Agent Graphs**: Perfect for precise control over communication patterns
- **Agent Workflows**: Optimal for sequential processes with clear dependencies

Each approach offers different trade-offs in terms of complexity, control, and collaboration patterns. The right choice depends on your specific use case and requirements.