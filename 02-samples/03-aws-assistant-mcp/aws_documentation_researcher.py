from mcp import StdioServerParameters, stdio_client
from strands import Agent, tool
from strands.tools.mcp import MCPClient
from strands_tools import file_write


@tool
def aws_documentation_researcher(query: str) -> str:
    """
    Process and respond AWS related queries.

    Args:
        query: The user's question

    Returns:
        A helpful response addressing user query
    """

    formatted_query = f"Analyze and respond to this question, providing clear explanations with examples where appropriate: {query}"
    response = str()

    try:
        documentation_mcp_server = MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command="uvx", args=["awslabs.aws-documentation-mcp-server@latest"]
                )
            )
        )

        with documentation_mcp_server:

            tools = documentation_mcp_server.list_tools_sync() + [file_write]
            # Create the research agent with specific capabilities
            research_agent = Agent(
                system_prompt="""You are a thorough AWS researcher specialized in finding accurate 
                information online. For each question:
                
                1. Determine what information you need
                2. Search the AWS Documentation for reliable information
                3. Extract key information and cite your sources
                4. Store important findings in memory for future reference
                5. Synthesize what you've found into a clear, comprehensive answer
                
                When researching, focus only on AWS documentation. Always provide citations 
                for the information you find.
                
                Finally output your response to a file in current directory.
                """,
                tools=tools,
            )
            response = str(research_agent(formatted_query))
            print("\n\n")

        if len(response) > 0:
            return response

        return "I apologize, but I couldn't properly analyze your question. Could you please rephrase or provide more context?"

    # Return specific error message for English queries
    except Exception as e:
        return f"Error processing your query: {str(e)}"


if __name__ == "__main__":
    aws_documentation_researcher("What is Amazon Bedrock")
