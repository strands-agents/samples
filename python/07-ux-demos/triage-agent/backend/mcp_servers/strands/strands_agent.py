from mcp.server import FastMCP
from strands import Agent
from strands_tools import http_request

# Create the MCP server
mcp = FastMCP("Strands Agent MCP Server")

REAL_ESTATE_SYSTEM_PROMPT = """
You are a real estate expert, you have years of knowledge and experience selling and buying thousands of homes. You offer
great advice and are happy to help others. You can also look up items on wikipedia to better undestand the areas user's are
asking about.
"""

@mcp.tool(
    name="real_estate_expert",           # Custom tool name for the LLM
    description="A very smart real estate agent who can answer your questions", # Custom description
)
def real_estate_agent(query: str) -> str:
    """
    Process and respond to real estate related questions
    """
    # Format the query for the math agent with clear instructions
    formatted_query = f"Answer the following question: {query}"
    
    try:
        print("Routed to Real Estate Expert")
        real_estate_agent = Agent(
            model="us.amazon.nova-pro-v1:0",
            system_prompt=REAL_ESTATE_SYSTEM_PROMPT,
            tools=[http_request], # Allow it to access the internet
        )
        response = real_estate_agent(formatted_query)
        return str(response)
        
    except Exception as e:
        return f"Error processing your query: {str(e)}"

if __name__ == "__main__":
    print("Starting Strands Agent MCP Server...")
    mcp.run(transport="stdio") 