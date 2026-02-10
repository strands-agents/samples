# AgentCore Concepts

Understanding the core concepts of Amazon Bedrock AgentCore will help you build better AI agents.

## What is AgentCore Runtime?

AgentCore Runtime is a **serverless compute environment** specifically designed for AI agents. Unlike traditional serverless platforms, it's optimized for:

- **Long-running conversations** - Agents can maintain context across multiple turns
- **Tool execution** - Native support for agent tools and function calling
- **Streaming responses** - Real-time token streaming to clients
- **Auto-scaling** - Scales from zero to handle traffic spikes

## Key Components

### 1. Runtime

The Runtime is where your agent code executes. Key features:

- **Container-based** - Your agent runs in a Docker container
- **Serverless** - No infrastructure to manage
- **Secure** - Isolated execution environment
- **Observable** - Built-in logging and metrics

### 2. Memory

AgentCore Memory provides persistent storage for agent state:

- **Short-term memory (STM)** - Conversation history within a session
- **Long-term memory (LTM)** - Facts and preferences across sessions
- **Semantic search** - Query memories by meaning, not just keywords

Example memory configuration:
```python
memory_config = AgentCoreMemoryConfig(
    memory_id="my-agent-memory",
    session_id="user-session-123",
    actor_id="user-456"
)
```

### 3. Gateway

Gateway enables your agent to access external tools and services:

- **MCP Protocol** - Model Context Protocol for tool integration
- **IAM Authentication** - Secure access to AWS services
- **Tool Discovery** - Dynamic tool registration

### 4. Identity

Identity management for multi-tenant agents:

- **JWT Validation** - Verify user tokens
- **Actor ID** - Unique identifier per user
- **Session Management** - Track conversations per user

## Agent Lifecycle

1. **Cold Start** - Container initializes (first request)
2. **Warm** - Container ready for requests
3. **Processing** - Agent handles user message
4. **Idle** - Waiting for next request
5. **Scale Down** - Container terminated after idle timeout

## Protocols Supported

AgentCore supports multiple agent protocols:

| Protocol | Description | Use Case |
|----------|-------------|----------|
| **AG-UI** | Agent-to-UI protocol | Rich web interfaces |
| **A2A** | Agent-to-Agent | Multi-agent systems |
| **MCP** | Model Context Protocol | Tool integration |

## Best Practices

- Use **streaming** for better user experience
- Implement **graceful degradation** for tool failures
- Configure **appropriate timeouts** for your use case
- Monitor **CloudWatch metrics** for performance insights

## Pricing Model

AgentCore uses a pay-per-use model:

- **Compute time** - Billed per second of execution
- **Memory** - Based on container memory allocation
- **Requests** - Per invocation charge
- **Data transfer** - Standard AWS data transfer rates
