from strands import Agent, tool
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters

@tool
def doc_retrieve(query:str) -> str:
    """
    Documentation retrival agent which is used to gather information about best practices of the given service

    Args:
        query (str): The name of the AWS service to get best practices for. For example: "Amazon S3", "Amazon EC2", etc.
        
    Returns:
        str: A summary of best practices and recommendations for the specified AWS service, extracted from official documentation.
        
    Example:
        >>> doc_retrieve("audit my Amazon S3 bucket for best practices, bucket name is testbucket101")
        "Best practices for Amazon S3:
         1. Use bucket policies to control access
         2. Enable versioning for data protection
         3. Configure lifecycle policies
         ..."    """


    system_prompt = """
    You are a helpful agent that is going to read the documentation and provide summary of the best practices for a service.
    
    """
    aws_client = MCPClient(
        lambda: stdio_client(StdioServerParameters(command="uvx", args=["awslabs.aws-documentation-mcp-server@latest"]))
    )

    with aws_client:
        try:
            agent = Agent(tools=aws_client.list_tools_sync(), system_prompt=system_prompt)
            response = agent(query)   
            

        except Exception as e:
            print(f"An error occurred: {e}")
