# Creating Tools with Strands SDK

This guide explains the different ways to create tools for your Strands Agents.

## Ways to Create Tools

### 1. Using the `@tool` Decorator

The simplest way to create a tool is by using the `@tool` decorator on a Python function:

```python
from strands import tool

@tool
def my_tool(param1: str, param2: int) -> str:
    """
    Description of what my tool does.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        
    Returns:
        Description of what is returned
    """
    # Dummy implementation
    return f"Result: {param1}, {param2}"
```

Note: This approach uses Python docstrings to document the tool and type hints for parameter validation

### 2. Using TOOL_SPEC Dictionary

For more control over tool definition, you can use the TOOL_SPEC dictionary approach:

```python
from strands.types.tools import ToolResult, ToolUse
from typing import Any

TOOL_SPEC = {
    "name": "my_tool",
    "description": "Description of what this tool does",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Description of first parameter"
                },
                "param2": {
                    "type": "integer",
                    "description": "Description of second parameter",
                    "default": 2
                }
            },
            "required": ["param1"]
        }
    }
}

# Function name must match tool name
def my_tool(tool: ToolUse, **kwargs: Any) -> ToolResult:
    tool_use_id = tool["toolUseId"]
    param1 = tool["input"].get("param1")
    param2 = tool["input"].get("param2", 2)
    
    # Tool implementation
    result = f"Result: {param1}, {param2}"
    
    return {
        "toolUseId": tool_use_id,
        "status": "success",
        "content": [{"text": result}]
    }
```

This approach gives you more control over input schema definition. Here you can define explicit handling of success and error states.

Note: This follows the Amazon Bedrock Converse API format

#### Usage

You can import the tool through a function or from another file as well like so:

```python
agent = Agent(tools=[my_tool])
# or 
agent = Agent(tools=["./my_tool.py"])
```

### 3. Using MCP (Model Context Protocol) Tools

You can also integrate external tools using the Model Context Protocol:

```python
from mcp import StdioServerParameters, stdio_client
from strands.tools.mcp import MCPClient

# Connect to an MCP server
mcp_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="uvx", args=["awslabs.aws-documentation-mcp-server@latest"]
        )
    )
)

# Use the tools in your agent
with mcp_client:
    tools = mcp_client.list_tools_sync()
    agent = Agent(tools=tools)
```

This approach connects to external tool providers through MCP, thus allowing tools from different servers. It supports both stdio and HTTP transports

## Best Practices

1. **Tool Naming**: Use clear, descriptive names for your tools
2. **Documentation**: Provide detailed descriptions of what the tool does and its parameters
3. **Error Handling**: Include proper error handling in your tools
4. **Parameter Validation**: Validate inputs before processing
5. **Return Values**: Return structured data that's easy for the agent to understand

## Examples

Check out the example notebooks in this directory:
- [Using MCP Tools](01-using-mcp-tools/mcp-agent.ipynb): Learn how to integrate MCP tools with your agent
- [Custom Tools](02-custom-tools/custom-tools-with-strands-agents.ipynb): Learn how to create and use custom tools

For more details, see the [Strands tools documentation](https://strandsagents.com/0.1.x/user-guide/concepts/tools/python-tools/).