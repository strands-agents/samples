#!/usr/bin/env python3
import argparse
import os
from strands import Agent
from strands.tools.mcp import MCPClient
from strands_tools import file_read, file_write
from mcp import StdioServerParameters, stdio_client
from dotenv import load_dotenv

load_dotenv()


def get_environment_variables():
    """Get environment variables with defaults and error handling."""
    # Get cluster endpoint (required)
    cluster_endpoint = os.getenv("DSQL_CLUSTER_ENDPOINT")
    
    if not cluster_endpoint:
        raise ValueError(
            "Error: DSQL_CLUSTER environment variable is not set.\n"
            "Please set it using .env file"
        )

    # Get region
    region = os.getenv("DSQL_CLUSTER_REGION")

    # Get database user (optional, defaults to admin)
    database_user = os.getenv("DSQL_DATABASE_USER", "admin")
    return {
        "cluster_endpoint": cluster_endpoint,
        "region": region,
        "database_user": database_user,
    }


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="DSQL client using strands Agent")
    parser.add_argument("prompt", help="Prompt to send to the agent")
    parser.add_argument(
        "--ro", action="store_true", help="Run in read-only mode (no writes allowed)"
    )

    # Parse arguments
    args = parser.parse_args()

    # Get environment variables with defaults and error handling
    env_vars = get_environment_variables()
    
    mcp_args = [
        "awslabs.aurora-dsql-mcp-server@latest",
        "--cluster_endpoint",
        env_vars["cluster_endpoint"],
        "--region",
        env_vars["region"],
        "--database_user",
        env_vars["database_user"],
        "--profile", "default"
    ]

    # Add --allow-writes flag if not in read-only mode
    if not args.ro:
        mcp_args.append("--allow-writes")

    # Create the DSQL MCP client with NPX, the cluster name, and the AWS region
    dsql_client = MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command="uvx", args=mcp_args
                )
            )
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
