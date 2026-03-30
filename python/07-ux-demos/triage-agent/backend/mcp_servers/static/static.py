from mcp.server import FastMCP
from typing import Annotated, List, Dict, Optional
import json
import os

# Create the MCP server
mcp = FastMCP("Static Response Server")

@mcp.tool(
    name="read_some_value",           # Custom tool name for the LLM
    description="Read a value from the data store", # Custom description
)
def read_value() -> str:
    """Perform a read operation"""
    return f"This is the response for a read operation"

@mcp.tool(description="Write some value")
def write_value(
    value: Annotated[                 # Custom type annotation
        str,
        "The value to write to the data store",
    ],
) -> str:
    """Write some value to a data store"""
    return f"Value '{value}' written successfully"

if __name__ == "__main__":
    print("Starting Static Response MCP Server...")
    mcp.run(transport="stdio") 