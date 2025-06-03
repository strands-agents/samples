# Getting Started with Strands Agents

This guide will help you understand the basic concepts of Strands Agents and get you up and running with your first agent.

## Prerequisites

- Python 3.10 or later
- AWS account configured with appropriate permissions
- Basic understanding of Python programming

## Installation

Install Strands Agents and the tools package using pip:

```bash
pip install strands-agents strands-agents-tools
```

## Basic Concepts

Strands Agents is a framework for building AI agents that can interact with AWS services and perform complex tasks. The key components are:

1. **Agent**: The core component that manages the conversation and orchestrates tools
2. **Model**: The underlying LLM (Large Language Model) that powers the agent
3. **Tools**: Functions that the agent can use to perform specific tasks
4. **Sessions and State**: Mechanisms for maintaining conversation history and agent state across interactions
5. **Agent Loop**: The process flow of how agents receive input, process it, and generate responses
6. **Context Management**: How agents maintain and manage conversation context, including memory and retrieval

## Quick Start Guide

The `01-first-agent.ipynb` notebook in this directory provides a comprehensive guide with code examples for:

1. **Creating a Simple Agent**: Learn how to initialize a basic agent with a system prompt
2. **Adding Tools**: Discover how to enhance your agent with built-in and custom tools
3. **Configuring Logging**: Set up proper logging for debugging and monitoring
4. **Customizing the Agent**: Choose different models and configure their parameters

## Running the Examples

This folder contains a getting-started notebook and a simple usecase to help you get started:

1. **01-first-agent.ipynb**: A Jupyter notebook with a comprehensive quickstart guide and a usecase.
Here we'll build:
![Architecture](./images/agent_with_tools.png)

and a Recipe Agent:

![Architecture](./images/interactive_recipe_agent.png)


2. **02-simple-interactive-usecase/**: A directory containing a simple interactive cooking/Recipe agent to be run via the CLI.


To run the interactive agent:

1. Navigate to the directory: `cd 02-simple-interactive-usecase`
2. Install the requirements: `pip install -r requirements.txt`
3. Run the script: `python recipe_bot.py`

## Resources

- Explore the [Strands documentation](https://strandsagents.com/latest/user-guide/quickstart/) for more detailed guides
- Learn more about [Sessions and State](https://strandsagents.com/latest/user-guide/concepts/agents/sessions-state)
- Understand the [Agent Loop](https://strandsagents.com/latest/user-guide/concepts/agents/agent-loop/)
- Dive into [Context Management](https://strandsagents.com/latest/user-guide/concepts/agents/context-management/)
- Check out the [strands-agents-tools](https://github.com/strands-agents/tools) repository for pre-implemented tools
- Try building your own task-specific agent by customizing the system prompt and adding relevant tools

Happy building with Strands Agents! 🚀