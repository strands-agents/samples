#!/usr/bin/env python3
import os
import unittest
from unittest.mock import MagicMock, patch

import pytest


class TestElastiCacheIntegration(unittest.TestCase):
    """Test cases for ElastiCache integration."""

    @patch("os.getenv")
    def test_get_elasticache_mcp_client(self, mock_getenv):
        """Test creating ElastiCache MCP client."""
        # Import here to avoid module-level import issues during testing
        from main import get_elasticache_mcp_client
        
        # Mock environment variables
        def mock_env(var, default=None):
            env_vars = {
                "AWS_REGION": "us-east-1",
                "AWS_PROFILE": "test-profile",
                "ELASTICACHE_MAX_RETRIES": "5",
                "ELASTICACHE_RETRY_MODE": "adaptive",
                "ELASTICACHE_CONNECT_TIMEOUT": "10",
                "ELASTICACHE_READ_TIMEOUT": "15",
                "COST_EXPLORER_MAX_RETRIES": "4",
                "COST_EXPLORER_RETRY_MODE": "standard",
                "COST_EXPLORER_CONNECT_TIMEOUT": "8",
                "COST_EXPLORER_READ_TIMEOUT": "12",
                "CLOUDWATCH_MAX_RETRIES": "3",
                "CLOUDWATCH_RETRY_MODE": "standard",
                "CLOUDWATCH_CONNECT_TIMEOUT": "7",
                "CLOUDWATCH_READ_TIMEOUT": "14",
                "CLOUDWATCH_LOGS_MAX_RETRIES": "6",
                "CLOUDWATCH_LOGS_RETRY_MODE": "adaptive",
                "CLOUDWATCH_LOGS_CONNECT_TIMEOUT": "9",
                "CLOUDWATCH_LOGS_READ_TIMEOUT": "18",
                "FIREHOSE_MAX_RETRIES": "4",
                "FIREHOSE_RETRY_MODE": "standard",
                "FIREHOSE_CONNECT_TIMEOUT": "6",
                "FIREHOSE_READ_TIMEOUT": "11"
            }
            return env_vars.get(var, default)
        
        mock_getenv.side_effect = mock_env
        
        # Mock MCPClient and StdioServerParameters
        with patch("main.MCPClient") as mock_mcp_client, \
             patch("main.stdio_client") as mock_stdio_client, \
             patch("main.StdioServerParameters") as mock_params:
            
            # Set up mocks
            mock_params.return_value = "mock_params"
            mock_stdio_client.return_value = "mock_stdio_client"
            mock_mcp_client.return_value = "mock_client"
            
            # Call the function
            client = get_elasticache_mcp_client()
            
            # Verify the function called the right methods with the right arguments
            mock_params.assert_called_once_with(
                command="uvx", 
                args=["awslabs.elasticache-mcp-server@latest"],
                env={
                    "AWS_REGION": "us-east-1",
                    "AWS_PROFILE": "test-profile",
                    "ELASTICACHE_MAX_RETRIES": "5",
                    "ELASTICACHE_RETRY_MODE": "adaptive",
                    "ELASTICACHE_CONNECT_TIMEOUT": "10",
                    "ELASTICACHE_READ_TIMEOUT": "15",
                    "COST_EXPLORER_MAX_RETRIES": "4",
                    "COST_EXPLORER_RETRY_MODE": "standard",
                    "COST_EXPLORER_CONNECT_TIMEOUT": "8",
                    "COST_EXPLORER_READ_TIMEOUT": "12",
                    "CLOUDWATCH_MAX_RETRIES": "3",
                    "CLOUDWATCH_RETRY_MODE": "standard",
                    "CLOUDWATCH_CONNECT_TIMEOUT": "7",
                    "CLOUDWATCH_READ_TIMEOUT": "14",
                    "CLOUDWATCH_LOGS_MAX_RETRIES": "6",
                    "CLOUDWATCH_LOGS_RETRY_MODE": "adaptive",
                    "CLOUDWATCH_LOGS_CONNECT_TIMEOUT": "9",
                    "CLOUDWATCH_LOGS_READ_TIMEOUT": "18",
                    "FIREHOSE_MAX_RETRIES": "4",
                    "FIREHOSE_RETRY_MODE": "standard",
                    "FIREHOSE_CONNECT_TIMEOUT": "6",
                    "FIREHOSE_READ_TIMEOUT": "11"
                }
            )
            mock_stdio_client.assert_called_once_with("mock_params")
            mock_mcp_client.assert_called_once()
            
            # Verify the function returned the expected client
            self.assertEqual(client, "mock_client")
    
    @patch("os.getenv")
    def test_get_valkey_mcp_client(self, mock_getenv):
        """Test creating Valkey MCP client."""
        # Import here to avoid module-level import issues during testing
        from main import get_valkey_mcp_client
        
        # Mock environment variables
        def mock_env(var, default=None):
            if var == "VALKEY_HOST":
                return "redis.example.com"
            elif var == "VALKEY_PORT":
                return "6380"
            elif var == "VALKEY_USERNAME":
                return "user"
            elif var == "VALKEY_PWD":
                return "password"
            elif var == "VALKEY_USE_SSL":
                return "True"
            elif var == "VALKEY_CLUSTER_MODE":
                return "True"
            return default
        
        mock_getenv.side_effect = mock_env
        
        # Mock MCPClient and StdioServerParameters
        with patch("main.MCPClient") as mock_mcp_client, \
             patch("main.stdio_client") as mock_stdio_client, \
             patch("main.StdioServerParameters") as mock_params:
            
            # Set up mocks
            mock_params.return_value = "mock_params"
            mock_stdio_client.return_value = "mock_stdio_client"
            mock_mcp_client.return_value = "mock_client"
            
            # Call the function
            client = get_valkey_mcp_client()
            
            # Verify the function called the right methods with the right arguments
            mock_params.assert_called_once_with(
                command="uvx", 
                args=["awslabs.valkey-mcp-server@latest"],
                env={
                    "VALKEY_HOST": "redis.example.com",
                    "VALKEY_PORT": "6380",
                    "VALKEY_USERNAME": "user",
                    "VALKEY_PWD": "password",
                    "VALKEY_USE_SSL": "true",
                    "VALKEY_CLUSTER_MODE": "true"
                }
            )
            mock_stdio_client.assert_called_once_with("mock_params")
            mock_mcp_client.assert_called_once()
            
            # Verify the function returned the expected client
            self.assertEqual(client, "mock_client")
    
    @patch("os.getenv")
    def test_get_memcached_mcp_client(self, mock_getenv):
        """Test creating Memcached MCP client."""
        # Import here to avoid module-level import issues during testing
        from main import get_memcached_mcp_client
        
        # Mock environment variables
        def mock_env(var, default=None):
            if var == "MEMCACHED_HOST":
                return "memcached.example.com"
            elif var == "MEMCACHED_PORT":
                return "11212"
            return default
        
        mock_getenv.side_effect = mock_env
        
        # Mock MCPClient and StdioServerParameters
        with patch("main.MCPClient") as mock_mcp_client, \
             patch("main.stdio_client") as mock_stdio_client, \
             patch("main.StdioServerParameters") as mock_params:
            
            # Set up mocks
            mock_params.return_value = "mock_params"
            mock_stdio_client.return_value = "mock_stdio_client"
            mock_mcp_client.return_value = "mock_client"
            
            # Call the function
            client = get_memcached_mcp_client()
            
            # Verify the function called the right methods with the right arguments
            mock_params.assert_called_once_with(
                command="uvx", 
                args=["awslabs.memcached-mcp-server@latest"],
                env={
                    "MEMCACHED_HOST": "memcached.example.com",
                    "MEMCACHED_PORT": "11212"
                }
            )
            mock_stdio_client.assert_called_once_with("mock_params")
            mock_mcp_client.assert_called_once()
            
            # Verify the function returned the expected client
            self.assertEqual(client, "mock_client")
            
    @patch("os.getenv")
    def test_get_aws_documentation_mcp_client(self, mock_getenv):
        """Test creating AWS Documentation MCP client."""
        # Import here to avoid module-level import issues during testing
        from main import get_aws_documentation_mcp_client
        
        # Mock environment variables
        mock_getenv.return_value = "aws-cn"
        
        # Mock MCPClient and StdioServerParameters
        with patch("main.MCPClient") as mock_mcp_client, \
             patch("main.stdio_client") as mock_stdio_client, \
             patch("main.StdioServerParameters") as mock_params:
            
            # Set up mocks
            mock_params.return_value = "mock_params"
            mock_stdio_client.return_value = "mock_stdio_client"
            mock_mcp_client.return_value = "mock_client"
            
            # Call the function
            client = get_aws_documentation_mcp_client()
            
            # Verify the function called the right methods with the right arguments
            mock_params.assert_called_once_with(
                command="uvx", 
                args=["awslabs.aws-documentation-mcp-server@latest"],
                env={"AWS_DOCUMENTATION_PARTITION": "aws-cn"}
            )
            mock_stdio_client.assert_called_once_with("mock_params")
            mock_mcp_client.assert_called_once()
            
            # Verify the function returned the expected client
            self.assertEqual(client, "mock_client")
    
    @patch("main.get_elasticache_mcp_client")
    @patch("main.get_valkey_mcp_client")
    @patch("main.get_memcached_mcp_client")
    @patch("main.get_aws_documentation_mcp_client")
    @patch("main.Agent")
    def test_main_with_all_engines(self, mock_agent, mock_aws_docs, mock_memcached, mock_valkey, mock_elasticache):
        """Test main function with all engines."""
        # Import here to avoid module-level import issues during testing
        import main
        from argparse import Namespace
        
        # Mock command line arguments
        args = Namespace(prompt="Test prompt", mcp_server="all", ro=False)
        with patch("main.argparse.ArgumentParser.parse_args", return_value=args):
            
            # Set up mocks
            mock_elasticache_client = MagicMock()
            mock_valkey_client = MagicMock()
            mock_memcached_client = MagicMock()
            mock_aws_docs_client = MagicMock()
            
            mock_elasticache.return_value = mock_elasticache_client
            mock_valkey.return_value = mock_valkey_client
            mock_memcached.return_value = mock_memcached_client
            mock_aws_docs.return_value = mock_aws_docs_client
            
            mock_elasticache_client.list_tools_sync.return_value = ["elasticache_tool"]
            mock_valkey_client.list_tools_sync.return_value = ["valkey_tool"]
            mock_memcached_client.list_tools_sync.return_value = ["memcached_tool"]
            mock_aws_docs_client.list_tools_sync.return_value = ["aws_docs_tool"]
            
            mock_agent_instance = MagicMock()
            mock_agent.return_value = mock_agent_instance
            mock_agent_instance.return_value = "Agent response"
            
            # Call the main function
            with patch("main.print") as mock_print:
                main.main()
            
            # Verify the clients were started and stopped
            mock_elasticache_client.start.assert_called_once()
            mock_valkey_client.start.assert_called_once()
            mock_memcached_client.start.assert_called_once()
            mock_aws_docs_client.start.assert_called_once()
            
            mock_elasticache_client.stop.assert_called_once()
            mock_valkey_client.stop.assert_called_once()
            mock_memcached_client.stop.assert_called_once()
            mock_aws_docs_client.stop.assert_called_once()
            
            # Verify the agent was created with the right tools
            mock_agent.assert_called_once()
            args, kwargs = mock_agent.call_args
            tools = kwargs.get("tools", [])
            self.assertIn("elasticache_tool", tools)
            self.assertIn("valkey_tool", tools)
            self.assertIn("memcached_tool", tools)
            self.assertIn("aws_docs_tool", tools)
            
            # Verify the agent was called with the right prompt
            mock_agent_instance.assert_called_once_with("Test prompt")
            
            # Verify the response was printed
            mock_print.assert_called_once_with("Agent response")


if __name__ == "__main__":
    unittest.main()
