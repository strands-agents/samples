<div align="center">
  <div>
    <a href="https://strandsagents.com">
      <img src="https://strandsagents.com/latest/assets/logo-auto.svg" alt="Strands Agents" width="55px" height="105px">
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
    ◆ <a href="https://github.com/strands-agents/tools">Tools</a>
    ◆ <a href="https://github.com/strands-agents/agent-builder">Agent Builder</a>
    ◆ <a href="https://github.com/strands-agents/mcp-server">MCP Server</a>
  </p>
</div>

Welcome to the Strands Agents Samples repository!

Explore easy-to-use examples to get started with <a href="https://strandsagents.com">Strands Agents</a>.

The examples in this repository are for **demonstration and educational purposes** only. They demonstrate concepts and techniques but are **not intended for direct use in production**. Always apply proper **security** and **testing** procedures before using in production environments.

## 📚 Table of Contents

- [📚 Table of Contents](#-table-of-contents)
- [🏁 Getting Started](#-getting-started)
  - [Step 1: Install Required Packages](#step-1-install-required-packages)
  - [Step 2: Setup Model Provider](#step-2-setup-model-provider)
  - [Step 3: Build Your First Strands Agent](#step-3-build-your-first-strands-agent)
  - [Step 4: Getting Started with the SDK](#step-4-getting-started-with-the-sdk)
  - [Step 5: Explore More Samples](#step-5-explore-more-samples)

## 🏁 Getting Started

### Step 1: Install Required Packages

```bash
pip install strands-agents
pip install strands-agents-tools
```

### Step 2: Setup Model Provider

Follow the instructions [here](https://strandsagents.com/latest/user-guide/quickstart/#model-providers) to configure your model provider and model access.

### Step 3: Build Your First Strands Agent

```python
from strands import Agent, tool
from strands_tools import calculator, current_time, python_repl

@tool
def letter_counter(word: str, letter: str) -> int:
    """
    Count the occurrences of a specific letter in a word.
    """
    if not isinstance(word, str) or not isinstance(letter, str):
        return 0
    if len(letter) != 1:
        raise ValueError("The 'letter' parameter must be a single character")
    return word.lower().count(letter.lower())

agent = Agent(tools=[calculator, current_time, python_repl, letter_counter])

message = """
I have 4 requests:

1. What is the time right now?
2. Calculate 3111696 / 74088
3. Tell me how many letter R's are in the word "strawberry" 🍓
4. Output a script that does what we just spoke about!
   Use your python tools to confirm that the script works before outputting it
"""

agent(message)
```

### Step 4: Getting Started with the SDK

Start with the [01-tutorials](./01-tutorials/) directory.
Create your [first agent](./01-tutorials/01-fundamentals/01-first-agent/) and explore notebook-based examples covering core functionalities.

### Step 5: Explore More Samples

Looking for inspiration?
Check out more examples in the [02-samples](./02-samples/) folder for real-world use cases.

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
