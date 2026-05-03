# A2A Protocol — Agent-to-Agent Communication

This tutorial shows how to use the **A2A (Agent-to-Agent) Protocol** to expose Strands agents as network services and connect them together. You'll learn to wrap agents as servers, invoke them remotely, discover their capabilities, stream responses, and compose remote agents as tools.

## Tutorial Details

| Information          | Details                                                                  |
|----------------------|--------------------------------------------------------------------------|
| **Strands Features** | `A2AServer`, `A2AAgent`, `A2AClientToolProvider`, agent cards, streaming |
| **Agent Pattern**    | Multi-agent via network protocol (server ↔ client)                       |
| **Tools**            | `calculator` from strands-agents-tools                                   |
| **Model**            | Amazon Nova Lite on Amazon Bedrock                                       |

## How It Works

1. **A2AServer** wraps any Strands `Agent` and serves it over HTTP with an auto-generated agent card
2. **A2AAgent** acts as a client that discovers and invokes remote agents
3. The agent card at `/.well-known/agent-card.json` advertises capabilities, skills, and streaming support
4. **A2AClientToolProvider** wraps remote agents as callable tools for an orchestrator agent

## Prerequisites

- Python 3.10 or later
- AWS account with [Amazon Bedrock](https://aws.amazon.com/bedrock/) access configured
- Basic familiarity with Strands Agents — see [01-first-agent](../01-first-agent/) if needed

## Tutorial Structure

```
16-a2a-protocol/
├── README.md
├── requirements.txt
└── a2a-protocol.ipynb
```

| File | Description |
|------|-------------|
| [a2a-protocol.ipynb](./a2a-protocol.ipynb) | Step-by-step notebook covering server setup, client invocation, agent card discovery, streaming, and tool composition |

## What You'll Learn

- **A2AServer**: wrap a Strands agent and serve it over HTTP
- **A2AAgent**: invoke a remote agent and get results
- **Agent card discovery**: inspect capabilities, skills (auto-derived from tools), and streaming support
- **Streaming patterns**: consume `A2AStreamEvent` for real-time responses
- **A2AClientToolProvider**: compose remote agents as tools for an orchestrator agent

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Then open [a2a-protocol.ipynb](./a2a-protocol.ipynb) from the `16-a2a-protocol/` directory.

## Related Tutorials

- [10-agents-as-tools](../10-agents-as-tools/) — composing agents locally (A2A extends this over the network)
- [04-streaming](../04-streaming/) — streaming fundamentals that A2A builds on
- [11-swarm](../11-swarm/) — alternative multi-agent pattern using swarms
