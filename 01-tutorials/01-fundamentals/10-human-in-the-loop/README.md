# Human-in-the-Loop (HITL) with Strands Agents

This guide will help you understand how to implement human-in-the-loop workflows with Strands Agents, enabling you to pause agent execution, request human input or approval, and resume based on that input.

## Prerequisites

- Python 3.10 or later
- AWS account configured with appropriate permissions
- Basic understanding of Python programming
- Familiarity with Strands Agents basics [(see Quickstart Guide)](https://strandsagents.com/latest/documentation/docs/user-guide/quickstart/)

## Installation

Install Strands Agents and the tools package using pip:

```bash
pip install strands-agents strands-agents-tools
```

## Basic Concepts

The interrupt system in Strands Agents allows you to build workflows that require human oversight. The key components are:

- **Interrupts**	- Mechanisms to pause agent execution and request human input
- **Hooks** - Intercept tool calls before execution using BeforeToolCallEvent
- **Tool Context** - Access interrupt functionality from within tools using tool_context.interrupt()
- **Session Management**	- Persist interrupt state and user preferences across sessions
- **Agent State**	- Store and retrieve user preferences with agent.state.set() and agent.state.get()

## What You'll Learn
The strands_hitl.ipynb notebook in this directory provides comprehensive examples for:

- **Understanding Interrupts**: Learn how the interrupt system pauses and resumes agent execution
- **Hook-Based Approvals**: Create approval workflows that intercept tool calls before execution
- **Tool-Based Interrupts**: Raise interrupts directly from within your tool definitions
- **Session Persistence**: Remember user preferences across sessions with FileSessionManager

Architecture:

![Architecture Patterns](/images/interrupt-patterns.png)

## Running the Examples
Open the notebook: strands_hitl.ipynb
Run cells sequentially to see each pattern in action
Interact with the approval prompts when requested

## Key Points to Remember
- Unique Names: Interrupt names must be unique within their scope (hook or tool)
- JSON-Serializable: Both reason and response must be JSON-serializable
- One at a Time: A single hook/tool can raise multiple interrupts sequentially, not simultaneously
- Concurrent Tools: All concurrently running tools can raise interrupts independently

Happy building with Strands Agents! 🚀