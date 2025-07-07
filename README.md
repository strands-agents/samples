# Strands Agents Samples & Patterns

A comprehensive collection of tutorials, samples, and reusable patterns for building AI agents with the [Strands SDK](https://strandsagents.com). This repository serves as both a learning resource and a pattern library for the Strands community.

## 🗂️ Repository Structure

### 📚 Learning Path (01-05 directories)

**Start here if you're new to Strands Agents**

- **[01-tutorials/](01-tutorials/)** - Step-by-step learning materials
  - Fundamentals, multi-agent systems, and deployment guides
- **[02-samples/](02-samples/)** - Complete application examples  
  - Real-world use cases and production-ready implementations
- **[03-integrations/](03-integrations/)** - Third-party service integrations
  - AWS services, external APIs, and tool connections
- **[04-UX-demos/](04-UX-demos/)** - User interface implementations
  - Streamlit apps, web interfaces, and deployment templates
- **[05-agentic-rag/](05-agentic-rag/)** - Advanced RAG patterns
  - Corrective RAG, adaptive systems, and retrieval patterns

### 🎯 Reusable Patterns (New!)

**Use these for quick implementation of specific features**

- **[agent-patterns/](agent-patterns/)** - Production-ready, discoverable patterns
  - Focused 2-4 service integrations following serverlessland.com model
  - Complete with metadata, testing, and deployment automation
- **[_templates/](\_templates/)** - Pattern creation templates
  - Standardized starting points for new patterns

## 🚀 Quick Start

### For Learning
If you're new to Strands Agents, start with the learning path:

```bash
# Begin with the fundamentals
cd 01-tutorials/01-fundamentals/01-first-agent
pip install -r requirements.txt
# Follow the README instructions
```

### For Implementation
If you need a specific feature, browse the patterns:

```bash
# Find and use a pattern
cd agent-patterns/websearch-agent
pip install -r requirements.txt
python src/agent.py
```

## 🎨 Featured Patterns

| Pattern | Description | Complexity | AWS Services |
|---------|-------------|------------|--------------|
| [**websearch-agent**](agent-patterns/websearch-agent) | Real-time web search with DuckDuckGo | Beginner | Bedrock |
| [**agent-orchestrator**](agent-patterns/agent-orchestrator) | Multi-agent coordination system | Intermediate | Bedrock |
| [**bedrock-knowledgebase-dynamodb**](agent-patterns/bedrock-knowledgebase-dynamodb) | RAG + persistent data operations | Advanced | Bedrock, DynamoDB, S3 |

[**Browse all patterns →**](agent-patterns/)

## 📖 Learning Journey

### 1. **Start with Fundamentals** (01-tutorials)
- Create your first agent
- Learn about tools and integrations  
- Understand multi-agent patterns
- Explore deployment options

### 2. **Study Real Applications** (02-samples)
- Restaurant assistant with reservations
- Personal assistant with multiple capabilities
- Data analysis and visualization agents
- Industry-specific implementations

### 3. **Explore Integrations** (03-integrations)
- AWS service connections
- Third-party API integrations
- Advanced observability patterns

### 4. **Build User Interfaces** (04-UX-demos)
- Streamlit web applications
- Interactive dashboards
- Deployment architectures

### 5. **Master Advanced RAG** (05-agentic-rag)
- Corrective retrieval systems
- Adaptive query processing
- Hybrid search approaches

### 6. **Use Production Patterns** (agent-patterns)
- Ready-to-deploy implementations
- Best practice examples
- Tested and validated code

## 🛠️ Contributing

### Adding Patterns
We welcome community contributions! To add a new pattern:

1. **Use a template**: `cp -r _templates/basic-agent agent-patterns/your-pattern`
2. **Follow naming**: `service1-service2-usecase` format
3. **Complete documentation**: README, metadata, tests
4. **Submit PR**: Our automation will validate your pattern

See our [Contributing Guide](docs/contributing.md) for detailed instructions.

### Improving Existing Content
- Fix bugs or improve documentation in existing tutorials/samples
- Add new examples or use cases
- Enhance testing and validation

## 🏗️ Pattern vs Tutorial vs Sample

| Type | Purpose | Structure | When to Use |
|------|---------|-----------|-------------|
| **Pattern** | Reusable integration template | Focused 2-4 services, standardized | Need specific functionality quickly |
| **Tutorial** | Step-by-step learning | Educational progression | Learning Strands concepts |
| **Sample** | Complete application example | Full-featured implementation | Understanding real-world usage |

## 📦 Installation

### Basic Setup
```bash
# Install Strands Agents
pip install strands-agents strands-agents-tools

# Clone this repository
git clone https://github.com/strands-agents/samples.git
cd samples
```

### AWS Configuration (for AWS patterns)
```bash
# Configure AWS CLI
aws configure

# Verify Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

## 📚 Documentation

- **[Strands Agents Documentation](https://strandsagents.com)** - Official SDK docs
- **[Pattern Documentation](docs/)** - Pattern-specific guides
- **[API Reference](https://strandsagents.com/api)** - Complete API documentation

## 🎯 Use Cases by Category

### 🤖 Basic Agents
- Conversational assistants
- Tool-calling agents  
- Simple automation

### 🔄 Multi-Agent Systems
- Hierarchical coordination
- Swarm intelligence
- Specialized teams

### 📚 Knowledge & Retrieval
- Document Q&A systems
- RAG implementations
- Information retrieval

### ☁️ AWS Integrations
- Bedrock model usage
- DynamoDB persistence
- S3 file processing
- Lambda deployment

### 🔧 Tool Integrations
- External API connections
- Database operations
- Web scraping
- File processing

### 🎨 UI/UX Patterns
- Web applications
- Chatbot interfaces
- Dashboard creation
- Mobile apps

## 🚦 Status & Roadmap

### Current Status
- ✅ Complete learning tutorials (01-05)
- ✅ Pattern framework implemented
- ✅ Automated validation pipeline
- ✅ Community contribution process

### Coming Soon
- 🔄 More AWS integration patterns
- 🔄 Advanced multi-agent patterns  
- 🔄 Mobile and web framework integrations
- 🔄 Industry-specific templates

## 💬 Community & Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/strands-agents/samples/issues)
- **Discussions**: [Ask questions and share ideas](https://github.com/strands-agents/samples/discussions)
- **Documentation**: [Official Strands docs](https://strandsagents.com)

## 📄 License

This project is licensed under the MIT-0 License - see the [LICENSE](LICENSE) file for details.

---

**Happy building with Strands Agents! 🚀**
