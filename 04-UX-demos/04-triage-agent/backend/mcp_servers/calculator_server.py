from mcp.server import FastMCP

# Create a new MCP server
mcp = FastMCP("Calculator Server")

@mcp.tool(description="Add two numbers together")
def add(x: float, y: float) -> float:
    """Add two numbers and return the result."""
    return x + y

@mcp.tool(description="Subtract second number from first number")
def subtract(x: float, y: float) -> float:
    """Subtract y from x and return the result."""
    return x - y

@mcp.tool(description="Multiply two numbers together")
def multiply(x: float, y: float) -> float:
    """Multiply two numbers and return the result."""
    return x * y

@mcp.tool(description="Divide first number by second number")
def divide(x: float, y: float) -> float:
    """Divide x by y and return the result."""
    if y == 0:
        raise ValueError("Cannot divide by zero")
    return x / y

if __name__ == "__main__":
    print("🔢 Starting Calculator MCP Server...")
    mcp.run(transport="stdio") 