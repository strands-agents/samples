# Strands Agents Patterns

Welcome to the Strands Agents Patterns repository - a collection of production-ready, reusable patterns for building AI agents with the Strands SDK. These patterns are designed to help you quickly implement common agent architectures and integrations.

## What are Strands Agent Patterns?

Strands Agent Patterns are focused, reusable templates that demonstrate specific integration patterns between Strands agents and various services, tools, or architectural approaches. Each pattern includes:

- **Complete source code** with clear documentation
- **Step-by-step deployment instructions** 
- **Metadata for discoverability** and categorization
- **Testing examples** and use cases
- **Cost estimates** and performance metrics
- **Next steps** for customization and extension

## Pattern Categories

### 🤖 [Basic Agents](categories/basic-agents.md)
Single-agent patterns demonstrating core Strands functionality, tool integration, and fundamental concepts.

### 🔄 [Multi-Agent Systems](categories/multi-agent-systems.md)
Patterns showing agent orchestration, swarm intelligence, hierarchical delegation, and agent-to-agent communication.

### 📚 [Knowledge & Retrieval](categories/knowledge-retrieval.md)
RAG (Retrieval-Augmented Generation) patterns, knowledge base integration, and information retrieval systems.

### ☁️ [AWS Integrations](categories/aws-integrations.md)
Patterns demonstrating integration with AWS services like Bedrock, DynamoDB, S3, Lambda, and more.

### 🔧 [Tool Integrations](categories/tool-integrations.md)
Patterns for integrating external APIs, databases, web services, and third-party tools.

### 🎨 [UI/UX Patterns](categories/ui-ux-patterns.md)
Frontend integration patterns for Streamlit, web applications, mobile apps, and user interfaces.

## Featured Patterns

<div class="grid cards" markdown>

-   :material-web: **Web Search Agent**

    ---

    Build a conversational AI agent with real-time web search capabilities using DuckDuckGo

    [:octicons-arrow-right-24: View Pattern](agent-patterns/websearch-agent)

-   :material-account-group: **Agent Orchestrator**

    ---

    Create hierarchical multi-agent systems with specialized assistants coordinated by an orchestrator

    [:octicons-arrow-right-24: View Pattern](agent-patterns/agent-orchestrator)

-   :material-aws: **Bedrock Knowledge Base + DynamoDB**

    ---

    Combine Amazon Bedrock Knowledge Base for RAG with DynamoDB for persistent data operations

    [:octicons-arrow-right-24: View Pattern](agent-patterns/bedrock-knowledgebase-dynamodb)

</div>

## Getting Started

### Quick Start

1. **Choose a pattern** that matches your use case
2. **Follow the deployment instructions** in the pattern's README
3. **Test the implementation** with the provided examples
4. **Customize** the pattern for your specific needs

### Prerequisites

Most patterns require:
- Python 3.10 or later
- AWS CLI configured (for AWS integration patterns)
- Strands Agents SDK: `pip install strands-agents strands-agents-tools`

### Pattern Structure

Each pattern follows a consistent structure:

```
pattern-name/
├── README.md                 # Pattern documentation
├── pattern-metadata.json     # Metadata for discovery
├── src/
│   └── agent.py             # Main implementation
├── requirements.txt          # Dependencies
├── tests/                   # Test files
└── examples/                # Usage examples
```

## Contributing Patterns

We welcome community contributions! To submit a new pattern:

1. **Use the pattern template** from `_templates/`
2. **Follow the naming convention**: `service1-service2-usecase`
3. **Include complete documentation** and metadata
4. **Test thoroughly** and provide examples
5. **Submit a pull request** with your pattern

See our [Contributing Guide](contributing.md) for detailed instructions.

## Design Principles

Strands Agent Patterns follow these principles:

- **🎯 Focused Scope**: Each pattern demonstrates 2-4 service integrations maximum
- **📋 Consistent Structure**: Standardized directory layout and documentation format
- **🚀 Production Ready**: Include error handling, logging, and deployment considerations
- **💰 Cost Transparent**: Clear cost estimates and optimization recommendations
- **🔧 Extensible**: Designed for easy customization and enhancement
- **📚 Educational**: Include learning objectives and next steps

## Community & Support

- **Documentation**: [Strands Agents Docs](https://strandsagents.com)
- **GitHub**: [strands-agents/samples](https://github.com/strands-agents/samples)
- **Issues**: Report bugs or request patterns
- **Discussions**: Share ideas and get help

## License

All patterns are licensed under the MIT-0 License, allowing you to use them freely in your projects without attribution requirements. 