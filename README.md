<div align="center">
  <div>
    <a href="https://strandsagents.com">
      <img src="https://strandsagents.com/latest/assets/logo-github.svg" alt="Strands Agents" width="55px" height="105px">
    </a>
  </div>

  <h1>
    Strands Agents Samples
  </h1>

  <h2>
    A model-driven approach to building AI agents in just a few lines of code.
  </h2>

  <div align="center">
    <a href="https://github.com/strands-agents/samples/graphs/commit-activity"><img alt="GitHub commit activity" src="https://img.shields.io/github/commit-activity/m/strands-agents/samples"/></a>
    <a href="https://github.com/strands-agents/samples/issues"><img alt="GitHub open issues" src="https://img.shields.io/github/issues/strands-agents/samples"/></a>
    <a href="https://github.com/strands-agents/samples/pulls"><img alt="GitHub open pull requests" src="https://img.shields.io/github/issues-pr/strands-agents/samples"/></a>
    <a href="https://github.com/strands-agents/samples/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/strands-agents/samples"/></a>
  </div>
  
  <p>
    <a href="https://strandsagents.com/">Documentation</a>
    ◆ <a href="https://github.com/strands-agents/samples">Samples</a>
    ◆ <a href="https://github.com/strands-agents/sdk-python">Python SDK</a>
    ◆ <a href="https://github.com/strands-agents/sdk-typescript">TypeScript SDK</a> <img src="https://img.shields.io/badge/NEW-brightgreen" alt="New"/>
    ◆ <a href="https://github.com/strands-agents/tools">Tools</a>
    ◆ <a href="https://github.com/strands-agents/agent-builder">Agent Builder</a>
    ◆ <a href="https://github.com/strands-agents/mcp-server">MCP Server</a>
  </p>
</div>

Welcome to the Strands Agents Samples repository!

Explore easy-to-use examples to get started with <a href="https://strandsagents.com">Strands Agents</a>.

The examples in this repository are for **demonstration and educational purposes** only. They demonstrate concepts and techniques but are **not intended for direct use in production**. Always apply proper **security** and **testing** procedures before using in production environments.

## Quick Start

<table>
<tr>
<td width="40%" valign="top">

### <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" width="24" height="24" alt="Python"/> Python

**Prerequisites:**
- Python 3.10 or higher
- pip package manager
  - Verify with: `pip --version` or `pip3 --version`
  - Usually comes bundled with Python 3.4+ installers from python.org
  - If pip is missing, install using one of these methods:
    ```bash
    # Method 1 - Use Python's built-in module
    python -m ensurepip --upgrade

    # Method 2 - Download and run the official installer
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python get-pip.py
    ```

**Step 1: Create Virtual Environment**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

**Step 2: Install**
```bash
pip install strands-agents strands-agents-tools
```

**Your First Agent:**
```python
from strands import Agent

agent = Agent()
response = agent("Hello! Tell me a joke.")
print(response)
```

[Explore Python tutorials →](./python/01-learn/)

</td>
<td width="60%" valign="top">

### <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/typescript/typescript-original.svg" width="24" height="24" alt="TypeScript"/> TypeScript

**Prerequisites:**
- Node.js 18 or higher
- npm or yarn package manager

**Install:**
```bash
npm install @strands-agents/sdk
```

**Your First Agent:**
```typescript
import { Agent } from "@strands-agents/sdk";

async function main() {
    const agent = new Agent({
        systemPrompt: "You are a helpful assistant."
    });

    const response = await agent.invoke("Hello! Tell me a joke.");
    console.log(response.toString());
}

main();
```

[Explore TypeScript tutorials →](./typescript/01-learn/)

</td>
</tr>
</table>

### Model Provider Setup

Follow the instructions [here](https://strandsagents.com/latest/user-guide/quickstart/#model-providers) to configure your model provider and model access.

## Explore the Repository

### <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" width="20" height="20"/> Python Samples

- **[01-learn](./python/01-learn/)** - SDK tutorials covering fundamentals, multi-agent systems, and streaming
- **[02-deploy](./python/02-deploy/)** - Deployment patterns for Lambda, Fargate, and AgentCore
- **[03-integrate](./python/03-integrate/)** - Integrations with AWS services, databases, and third-party tools
- **[04-industry-use-cases](./python/04-industry-use-cases/)** - Industry applications (finance, healthcare, retail, productivity, etc.)
- **[05-technical-use-cases](./python/05-technical-use-cases/)** - Architectural patterns including Agentic RAG
- **[06-evaluate](./python/06-evaluate/)** - Evaluation tutorials and testing patterns
- **[07-ux-demos](./python/07-ux-demos/)** - Full-stack applications with user interfaces
- **[08-edge](./python/08-edge/)** - Edge device integrations including physical AI and robotics

### <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/typescript/typescript-original.svg" width="20" height="20"/> TypeScript Samples

- **[01-learn](./typescript/01-learn/)** - SDK tutorials for the TypeScript SDK
- **[02-deploy](./typescript/02-deploy/)** - Deployment patterns for AgentCore

## Contributing ❤️

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details on:
- Reporting bugs & features
- Development setup
- Contributing via Pull Requests
- Code of Conduct
- Reporting of security issues

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.
