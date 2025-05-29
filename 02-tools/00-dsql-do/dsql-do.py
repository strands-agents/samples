#!/usr/bin/env python3
# DSQL-do is a little tool for doing stuff to DSQL clusters using natural language.
# See README.md for how to set it up and some examples.
import argparse
import os
from strands import Agent, tool
from strands.tools.mcp import MCPClient
from strands_tools import file_read, file_write
from mcp import stdio_client, StdioServerParameters

def get_environment_variables():
    """Get environment variables with defaults and error handling."""
    # Get cluster endpoint (required)
    cluster_endpoint = os.environ.get("DSQL_CLUSTER")
    if not cluster_endpoint:
        raise ValueError(
            "Error: DSQL_CLUSTER environment variable is not set.\n"
            "Please set it using: export DSQL_CLUSTER=<your_cluster_name>"
        )
    
    # Get region (optional, defaults to us-east-1)
    region = os.environ.get("DSQL_CLUSTER_REGION", "us-east-1")
    
    # Get database user (optional, defaults to admin)
    database_user = os.environ.get("DSQL_DATABASE_USER", "admin")

    # Get the path to the DSQL MCP server. This is a short-term work-around until the server is in the AWS MCP package.
    mcp_path = os.environ.get("DSQL_MCP_PATH", "")
    
    return {
        "cluster_endpoint": cluster_endpoint,
        "region": region,
        "database_user": database_user,
        "mcp_path": mcp_path
    }

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="DSQL client using strands Agent")
    parser.add_argument("prompt", help="Prompt to send to the agent")
    parser.add_argument("--ro", action="store_true", help="Run in read-only mode (no writes allowed)")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Get environment variables with defaults and error handling
    env_vars = get_environment_variables()
    
    # Prepare arguments for the MCP server
    mcp_args = ["--with-editable", 
                env_vars["mcp_path"], 
                "awslabs.aurora-dsql-mcp-server",
                "--cluster_endpoint", env_vars["cluster_endpoint"],
                "--region", env_vars["region"],
                "--database_user", env_vars["database_user"]]
    
    # Add --allow-writes flag if not in read-only mode
    if not args.ro:
        mcp_args.append("--allow-writes")
    
    # Create the DSQL MCP client with NPX, the cluster name, and the AWS region
    dsql_client = MCPClient(
        lambda: stdio_client(StdioServerParameters(
            command="uvx", 
            args=mcp_args
        ))
    )
    
    # Execute the prompt
    with dsql_client:
        tools = dsql_client.list_tools_sync()
        tools.extend([file_read, file_write])
        agent = Agent(tools=tools)
        try:
            response = agent(args.prompt)
            print(response)
        except Exception as e:
            print(f"Error executing prompt: {e}")

if __name__ == "__main__":
    main()