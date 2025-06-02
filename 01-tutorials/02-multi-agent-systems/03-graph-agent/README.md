### What is an Agent Graph?

An Agent Graph is a collection of AI agents organized in a specific topology where:

- **Nodes**: Individual agents with specific roles, identity, tools and system prompts
- **Edges**: Communication paths between agents
- **Topologies**: Different network structures (star, mesh, hierarchical)

### Common Topologies

1. **Star Topology**: A central agent coordinates with multiple specialized agents

```mermaid
graph TD
    subgraph "Star Topology"
        Central[Central Agent] --> Agent1[Agent 1]
        Central --> Agent2[Agent 2]
        Central --> Agent3[Agent 3]
        Central --> Agent4[Agent 4]
        Agent1 --> Central
        Agent2 --> Central
        Agent3 --> Central
        Agent4 --> Central
    end
```
2. **Mesh Topology**: All agents can communicate directly with each other

```mermaid
graph TD
    subgraph "Mesh Topology"
        MAgent1[Agent 1] <--> MAgent2[Agent 2]
        MAgent1 <--> MAgent3[Agent 3]
        MAgent1 <--> MAgent4[Agent 4]
        MAgent2 <--> MAgent3
        MAgent2 <--> MAgent4
        MAgent3 <--> MAgent4
    end
```
3. **Hierarchical Topology**: Agents are organized in layers with defined reporting structures

```mermaid
graph TD
    subgraph "Hierarchical Topology"
        HAgent1[Executive Agent] --> HAgent2[Manager 1]
        HAgent1 --> HAgent3[Manager 2]
        HAgent2 --> HAgent4[Worker 1]
        HAgent2 --> HAgent5[Worker 2]
        HAgent3 --> HAgent6[Worker 3]
        HAgent3 --> HAgent7[Worker 4]
    end
```

### Example

To get started with building agents with these patterns. Navigate to `graph.ipynb` to build a graph using the **star topology**.