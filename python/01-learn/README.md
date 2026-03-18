# Strands Agents SDK Fundamentals (Python)

Step-by-step guides from basic agent creation to multi-agent orchestration.

## Index

| Folder | SDK Feature | Description |
|--------|-------------|-------------|
| [`01-first-agent`](./01-first-agent/) | `Agent` class | Create your first agent with system prompts |
| [`02-tools-and-mcp`](./02-tools-and-mcp/) | `@tool` decorator, MCP | Build custom tools and connect MCP servers |
| [`03-model-providers`](./03-model-providers/) | `BedrockModel`, `OllamaModel`, `LiteLLMModel` | Switch between Bedrock, Ollama, and OpenAI |
| [`04-streaming`](./04-streaming/) | `stream_async`, callbacks | Stream responses in async/FastAPI apps |
| [`05-guardrails`](./05-guardrails/) | `guardrails` parameter | Add content filtering with Bedrock Guardrails |
| [`06-memory`](./06-memory/) | Memory tools | Persist agent memory across sessions |
| [`07-aws-services`](./07-aws-services/) | `retrieve` tool, `BedrockModel` | Connect to Knowledge Bases and DynamoDB |
| [`08-observability`](./08-observability/) | Tracing, evaluation | Trace with Langfuse, evaluate with RAGAS |
| [`09-bidi-streaming`](./09-bidi-streaming/) | `BidiAgent` | Build real-time voice agents |
| [`10-agents-as-tools`](./10-agents-as-tools/) | Hierarchical agents | Compose agents as callable tools |
| [`11-swarm`](./11-swarm/) | `Swarm` class | Build self-organizing agent teams |
| [`12-graph`](./12-graph/) | `GraphBuilder` | Create deterministic agent workflows |
| [`13-human-in-the-loop`](./13-human-in-the-loop/) | Interrupts, hooks | Implement approval workflows with human oversight |

## Getting Started

Start with [`01-first-agent`](./01-first-agent/) if you're new to Strands Agents, then progress in order.

[Strands Agents Documentation](https://strandsagents.com/)
