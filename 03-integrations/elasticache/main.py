#!/usr/bin/env python3
import argparse
import os
from strands import Agent
from strands.tools.mcp import MCPClient
from strands_tools import file_read, file_write
from mcp import StdioServerParameters, stdio_client
from dotenv import load_dotenv

load_dotenv()


def get_elasticache_mcp_client(readonly=False):
    """Create and return an ElastiCache MCP client."""
    args = ["awslabs.elasticache-mcp-server@latest"]
    
    # Add readonly flag if specified
    if readonly:
        args.append("--readonly")
    
    # Create environment variables dictionary
    env = {}
    
    # AWS Configuration
    env["AWS_REGION"] = os.getenv("AWS_REGION", "us-west-2")
    if os.getenv("AWS_PROFILE"):
        env["AWS_PROFILE"] = os.getenv("AWS_PROFILE")
    
    # ElastiCache Connection Settings
    if os.getenv("ELASTICACHE_MAX_RETRIES"):
        env["ELASTICACHE_MAX_RETRIES"] = os.getenv("ELASTICACHE_MAX_RETRIES")
    if os.getenv("ELASTICACHE_RETRY_MODE"):
        env["ELASTICACHE_RETRY_MODE"] = os.getenv("ELASTICACHE_RETRY_MODE")
    if os.getenv("ELASTICACHE_CONNECT_TIMEOUT"):
        env["ELASTICACHE_CONNECT_TIMEOUT"] = os.getenv("ELASTICACHE_CONNECT_TIMEOUT")
    if os.getenv("ELASTICACHE_READ_TIMEOUT"):
        env["ELASTICACHE_READ_TIMEOUT"] = os.getenv("ELASTICACHE_READ_TIMEOUT")
    
    # Cost Explorer Settings
    if os.getenv("COST_EXPLORER_MAX_RETRIES"):
        env["COST_EXPLORER_MAX_RETRIES"] = os.getenv("COST_EXPLORER_MAX_RETRIES")
    if os.getenv("COST_EXPLORER_RETRY_MODE"):
        env["COST_EXPLORER_RETRY_MODE"] = os.getenv("COST_EXPLORER_RETRY_MODE")
    if os.getenv("COST_EXPLORER_CONNECT_TIMEOUT"):
        env["COST_EXPLORER_CONNECT_TIMEOUT"] = os.getenv("COST_EXPLORER_CONNECT_TIMEOUT")
    if os.getenv("COST_EXPLORER_READ_TIMEOUT"):
        env["COST_EXPLORER_READ_TIMEOUT"] = os.getenv("COST_EXPLORER_READ_TIMEOUT")
    
    # CloudWatch Settings
    if os.getenv("CLOUDWATCH_MAX_RETRIES"):
        env["CLOUDWATCH_MAX_RETRIES"] = os.getenv("CLOUDWATCH_MAX_RETRIES")
    if os.getenv("CLOUDWATCH_RETRY_MODE"):
        env["CLOUDWATCH_RETRY_MODE"] = os.getenv("CLOUDWATCH_RETRY_MODE")
    if os.getenv("CLOUDWATCH_CONNECT_TIMEOUT"):
        env["CLOUDWATCH_CONNECT_TIMEOUT"] = os.getenv("CLOUDWATCH_CONNECT_TIMEOUT")
    if os.getenv("CLOUDWATCH_READ_TIMEOUT"):
        env["CLOUDWATCH_READ_TIMEOUT"] = os.getenv("CLOUDWATCH_READ_TIMEOUT")
    
    # CloudWatch Logs Settings
    if os.getenv("CLOUDWATCH_LOGS_MAX_RETRIES"):
        env["CLOUDWATCH_LOGS_MAX_RETRIES"] = os.getenv("CLOUDWATCH_LOGS_MAX_RETRIES")
    if os.getenv("CLOUDWATCH_LOGS_RETRY_MODE"):
        env["CLOUDWATCH_LOGS_RETRY_MODE"] = os.getenv("CLOUDWATCH_LOGS_RETRY_MODE")
    if os.getenv("CLOUDWATCH_LOGS_CONNECT_TIMEOUT"):
        env["CLOUDWATCH_LOGS_CONNECT_TIMEOUT"] = os.getenv("CLOUDWATCH_LOGS_CONNECT_TIMEOUT")
    if os.getenv("CLOUDWATCH_LOGS_READ_TIMEOUT"):
        env["CLOUDWATCH_LOGS_READ_TIMEOUT"] = os.getenv("CLOUDWATCH_LOGS_READ_TIMEOUT")
    
    # Firehose Settings
    if os.getenv("FIREHOSE_MAX_RETRIES"):
        env["FIREHOSE_MAX_RETRIES"] = os.getenv("FIREHOSE_MAX_RETRIES")
    if os.getenv("FIREHOSE_RETRY_MODE"):
        env["FIREHOSE_RETRY_MODE"] = os.getenv("FIREHOSE_RETRY_MODE")
    if os.getenv("FIREHOSE_CONNECT_TIMEOUT"):
        env["FIREHOSE_CONNECT_TIMEOUT"] = os.getenv("FIREHOSE_CONNECT_TIMEOUT")
    if os.getenv("FIREHOSE_READ_TIMEOUT"):
        env["FIREHOSE_READ_TIMEOUT"] = os.getenv("FIREHOSE_READ_TIMEOUT")
    
    return MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="uvx", args=args, env=env
            )
        )
    )


def get_valkey_mcp_client(readonly=False):
    """Create and return a Valkey MCP client."""
    args = ["awslabs.valkey-mcp-server@latest"]
    
    # Add readonly flag if specified
    if readonly:
        args.append("--readonly")
    
    # Create environment variables dictionary
    env = {}
    
    # Get connection details from environment variables
    host = os.getenv("VALKEY_HOST", "127.0.0.1")
    port = os.getenv("VALKEY_PORT", "6379")
    username = os.getenv("VALKEY_USERNAME")
    password = os.getenv("VALKEY_PWD")
    use_ssl = os.getenv("VALKEY_USE_SSL", "False").lower() == "true"
    cluster_mode = os.getenv("VALKEY_CLUSTER_MODE", "False").lower() == "true"
    
    # Add environment variables to env dictionary
    env["VALKEY_HOST"] = host
    env["VALKEY_PORT"] = port
    if username:
        env["VALKEY_USERNAME"] = username
    if password:
        env["VALKEY_PWD"] = password
    env["VALKEY_USE_SSL"] = "true" if use_ssl else "false"
    env["VALKEY_CLUSTER_MODE"] = "true" if cluster_mode else "false"
    
    return MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="uvx", args=args, env=env
            )
        )
    )


def get_memcached_mcp_client(readonly=False):
    """Create and return a Memcached MCP client."""
    args = ["awslabs.memcached-mcp-server@latest"]
    
    # Add readonly flag if specified
    if readonly:
        args.append("--readonly")
    
    # Create environment variables dictionary
    env = {}
    
    # Get connection details from environment variables
    host = os.getenv("MEMCACHED_HOST", "127.0.0.1")
    port = os.getenv("MEMCACHED_PORT", "11211")
    
    # Add environment variables to env dictionary
    env["MEMCACHED_HOST"] = host
    env["MEMCACHED_PORT"] = port
    
    return MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="uvx", args=args, env=env
            )
        )
    )


def get_aws_documentation_mcp_client():
    """Create and return an AWS Documentation MCP client."""
    args = ["awslabs.aws-documentation-mcp-server@latest"]
    
    # Create environment variables dictionary
    env = {}
    
    # Get partition from environment variable or use default
    partition = os.getenv("AWS_DOCUMENTATION_PARTITION", "aws")
    env["AWS_DOCUMENTATION_PARTITION"] = partition
    
    return MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="uvx", args=args, env=env
            )
        )
    )


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="ElastiCache client using strands Agent")
    parser.add_argument("prompt", help="Prompt to send to the agent")
    parser.add_argument(
        "--mcp-server", 
        choices=["elasticache", "valkey", "memcached", "aws-docs", "all"], 
        default="all",
        help="Specify which MCP server to use (elasticache, valkey, memcached, aws-docs, or all)"
    )
    parser.add_argument(
        "--ro", action="store_true", help="Run in read-only mode (no writes allowed)"
    )
    parser.add_argument(
        "--model", 
        default=os.getenv("STRANDS_MODEL_ID", "anthropic.claude-3-7-sonnet-20250219-v1:0"),
        help="Model ID to use for the agent (default: from STRANDS_MODEL_ID env var or Claude 3 Sonnet)"
    )

    # Parse arguments
    args = parser.parse_args()
    
    # Initialize clients based on the selected MCP server
    clients = []
    
    if args.mcp_server in ["elasticache", "all"]:
        try:
            elasticache_client = get_elasticache_mcp_client(readonly=args.ro)
            clients.append(elasticache_client)
        except Exception as e:
            print(f"Warning: Failed to initialize ElastiCache client: {e}")
    
    if args.mcp_server in ["valkey", "all"]:
        try:
            valkey_client = get_valkey_mcp_client(readonly=args.ro)
            clients.append(valkey_client)
        except Exception as e:
            print(f"Warning: Failed to initialize Valkey client: {e}")
    
    if args.mcp_server in ["memcached", "all"]:
        try:
            memcached_client = get_memcached_mcp_client(readonly=args.ro)
            clients.append(memcached_client)
        except Exception as e:
            print(f"Warning: Failed to initialize Memcached client: {e}")
            
    if args.mcp_server in ["aws-docs", "all"]:
        try:
            aws_docs_client = get_aws_documentation_mcp_client()
            clients.append(aws_docs_client)
        except Exception as e:
            print(f"Warning: Failed to initialize AWS Documentation client: {e}")
    
    if not clients:
        print("Error: No clients were successfully initialized.")
        return
    
    # Execute the prompt with all selected clients
    tools = [file_read, file_write]
    
    # Start all clients and collect their tools
    for client in clients:
        client.start()
        tools.extend(client.list_tools_sync())
    
    try:
        agent = Agent(tools=tools, model=args.model)
        response = agent(args.prompt)
        print(response)
    except Exception as e:
        print(f"Error executing prompt: {e}")
    finally:
        # Stop all clients
        for client in clients:
            client.stop(None, None, None)  # Provide required arguments for context manager exit method


if __name__ == "__main__":
    main()
