"""TCP tool for Strands Agents to function as both server and client.

This module provides TCP server and client functionality for Strands Agents,
allowing them to communicate over TCP/IP networks. The tool runs server operations
in background threads, enabling concurrent communication without blocking the main agent.

Key Features:
1. TCP Server: Listen for incoming connections and process them with an agent
2. TCP Client: Connect to remote TCP servers and exchange messages
3. Background Processing: Server runs in a background thread
4. Per-Connection Agents: Creates a fresh agent for each client connection

Usage with Strands Agent:

```python
from strands import Agent
from maxs.tools import tcp

agent = Agent(tools=[tcp])

# Start a TCP server
result = agent.tool.tcp(
    action="start_server",
    host="127.0.0.1",
    port=8000,
    system_prompt="You are a helpful TCP server assistant.",
)

# Connect to a TCP server as client
result = agent.tool.tcp(
    action="client_send", host="127.0.0.1", port=8000, message="Hello, server!"
)

# Stop the TCP server
result = agent.tool.tcp(action="stop_server", port=8000)
```

See the tcp function docstring for more details on configuration options and parameters.
"""

import logging
import socket
import threading
import time
from typing import Any

from strands import Agent, tool

logger = logging.getLogger(__name__)

# Global registry to store server threads
SERVER_THREADS: dict[int, dict[str, Any]] = {}


def handle_client(
    client_socket: socket.socket,
    client_address: tuple,
    system_prompt: str,
    buffer_size: int,
    model: Any,
    parent_tools: list | None = None,
    callback_handler: Any = None,
    trace_attributes: dict | None = None,
) -> None:
    """Handle a client connection in the TCP server.

    Args:
        client_socket: The socket for the client connection
        client_address: The address of the client
        system_prompt: System prompt for creating a new agent for this connection
        buffer_size: Size of the message buffer
        model: Model instance from parent agent
        parent_tools: Tools inherited from the parent agent
        callback_handler: Callback handler from parent agent
        trace_attributes: Trace attributes from the parent agent
    """
    logger.info(f"Connection established with {client_address}")

    # Create a fresh agent instance for this client connection
    connection_agent = Agent(
        model=model,
        messages=[],
        tools=parent_tools or [],
        callback_handler=callback_handler,
        system_prompt=system_prompt,
        trace_attributes=trace_attributes or {},
    )

    try:
        # Send welcome message
        welcome_msg = "Welcome to Strands TCP Server! Send a message or 'exit' to close the connection.\n"
        client_socket.sendall(welcome_msg.encode())

        while True:
            # Receive data from the client
            data = client_socket.recv(buffer_size)

            if not data:
                logger.info(f"Client {client_address} disconnected")
                break

            message = data.decode().strip()
            logger.info(f"Received from {client_address}: {message}")

            if message.lower() == "exit":
                client_socket.sendall(b"Connection closed by client request.\n")
                logger.info(f"Client {client_address} requested to exit")
                break

            # Process the message with the connection-specific agent
            response = connection_agent(message)
            response_text = str(response)

            # Send the response back to the client
            client_socket.sendall((response_text + "\n").encode())

    except Exception as e:
        logger.error(f"Error handling client {client_address}: {e}")
    finally:
        client_socket.close()
        logger.info(f"Connection with {client_address} closed")


def run_server(
    host: str,
    port: int,
    system_prompt: str,
    max_connections: int,
    buffer_size: int,
    parent_agent: Agent | None = None,
) -> None:
    """Run a TCP server that processes client requests with per-connection Strands agents.

    Args:
        host: Host address to bind the server
        port: Port number to bind the server
        system_prompt: System prompt for the server agents
        max_connections: Maximum number of concurrent connections
        buffer_size: Size of the message buffer
        parent_agent: Parent agent to inherit tools from
    """
    # Store server state
    SERVER_THREADS[port]["running"] = True
    SERVER_THREADS[port]["connections"] = 0
    SERVER_THREADS[port]["start_time"] = time.time()

    # Get model, tools, callback_handler and trace attributes from parent agent
    model = None
    callback_handler = None
    parent_tools = []
    trace_attributes = {}
    if parent_agent:
        model = parent_agent.model
        callback_handler = parent_agent.callback_handler
        parent_tools = list(parent_agent.tool_registry.registry.values())
        trace_attributes = parent_agent.trace_attributes

    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((host, port))
        server_socket.listen(max_connections)
        logger.info(f"TCP Server listening on {host}:{port}")

        SERVER_THREADS[port]["socket"] = server_socket

        while SERVER_THREADS[port]["running"]:
            # Set a timeout to check periodically if the server should stop
            server_socket.settimeout(1.0)

            try:
                # Accept client connection
                client_socket, client_address = server_socket.accept()
                SERVER_THREADS[port]["connections"] += 1

                # Handle client in a new thread with a fresh agent
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(
                        client_socket,
                        client_address,
                        system_prompt,
                        buffer_size,
                        model,
                        parent_tools,
                        callback_handler,
                        trace_attributes,
                    ),
                )
                client_thread.daemon = True
                client_thread.start()

            except TimeoutError:
                # This is expected due to the timeout, allows checking if server should stop
                pass
            except Exception as e:
                if SERVER_THREADS[port]["running"]:
                    logger.error(f"Error accepting connection: {e}")

    except Exception as e:
        logger.error(f"Server error on {host}:{port}: {e}")
    finally:
        try:
            server_socket.close()
        except OSError:
            # Socket already closed, safe to ignore
            pass
        logger.info(f"TCP Server on {host}:{port} stopped")
        SERVER_THREADS[port]["running"] = False


@tool
def tcp(
    action: str,
    host: str = "127.0.0.1",
    port: int = 8000,
    system_prompt: str = "You are a helpful TCP server assistant.",
    message: str = "",
    timeout: int = 90,
    buffer_size: int = 4096,
    max_connections: int = 5,
    agent: Any = None,
) -> dict:
    """Create and manage TCP servers and clients for network communication with connection handling.

    This function provides TCP server and client functionality for Strands agents,
    allowing them to communicate over TCP/IP networks. Servers run in background
    threads with a new, fresh agent instance for each client connection.

    How It Works:
    ------------
    1. Server Mode:
       - Starts a TCP server in a background thread
       - Creates a dedicated agent for EACH client connection
       - Inherits tools from the parent agent
       - Processes client messages and returns responses

    2. Client Mode:
       - Connects to a TCP server
       - Sends messages and receives responses
       - Maintains stateless connections (no persistent sessions)

    3. Management:
       - Track server status and statistics
       - Stop servers gracefully
       - Monitor connections and performance

    Common Use Cases:
    ---------------
    - Network service automation
    - Inter-agent communication
    - Remote command and control
    - API gateway implementation
    - IoT device management

    Args:
        action: Action to perform (start_server, stop_server, get_status, client_send)
        host: Host address for server or client connection
        port: Port number for server or client connection
        system_prompt: System prompt for the server agent (for start_server)
        message: Message to send to the TCP server (for client_send action)
        timeout: Connection timeout in seconds (default: 90)
        buffer_size: Size of the message buffer in bytes (default: 4096)
        max_connections: Maximum number of concurrent connections (default: 5)

    Returns:
        Dictionary containing status and response content

    Notes:
        - Server instances persist until explicitly stopped
        - Each client connection gets its own agent instance
        - Connection agents inherit tools from the parent agent
        - Client connections are stateless
    """
    # Get parent agent from tool context if available
    parent_agent = agent

    if action == "start_server":
        # Check if server already running on this port
        if port in SERVER_THREADS and SERVER_THREADS[port].get("running", False):
            return {
                "status": "error",
                "content": [
                    {"text": f"❌ Error: TCP Server already running on port {port}"}
                ],
            }

        # Create server thread
        SERVER_THREADS[port] = {"running": False}
        server_thread = threading.Thread(
            target=run_server,
            args=(
                host,
                port,
                system_prompt,
                max_connections,
                buffer_size,
                parent_agent,
            ),
        )
        server_thread.daemon = True
        server_thread.start()

        # Wait briefly to ensure server starts
        time.sleep(0.5)

        if not SERVER_THREADS[port].get("running", False):
            return {
                "status": "error",
                "content": [
                    {"text": f"❌ Error: Failed to start TCP Server on {host}:{port}"}
                ],
            }

        return {
            "status": "success",
            "content": [
                {"text": f"✅ TCP Server started successfully on {host}:{port}"},
                {"text": f"System prompt: {system_prompt}"},
                {"text": "Server creates a new agent instance for each connection"},
            ],
        }

    elif action == "stop_server":
        if port not in SERVER_THREADS or not SERVER_THREADS[port].get("running", False):
            return {
                "status": "error",
                "content": [
                    {"text": f"❌ Error: No TCP Server running on port {port}"}
                ],
            }

        # Stop the server
        SERVER_THREADS[port]["running"] = False

        # Close socket if it exists
        if "socket" in SERVER_THREADS[port]:
            try:
                SERVER_THREADS[port]["socket"].close()
            except OSError:
                # Socket already closed, safe to ignore
                pass

        # Wait briefly to ensure server stops
        time.sleep(1.0)

        connections = SERVER_THREADS[port].get("connections", 0)
        uptime = time.time() - SERVER_THREADS[port].get("start_time", time.time())

        # Clean up server thread data
        del SERVER_THREADS[port]

        return {
            "status": "success",
            "content": [
                {"text": f"✅ TCP Server on port {port} stopped successfully"},
                {
                    "text": f"Statistics: {connections} connections handled, uptime {uptime:.2f} seconds"
                },
            ],
        }

    elif action == "get_status":
        if not SERVER_THREADS:
            return {
                "status": "success",
                "content": [{"text": "No TCP Servers running"}],
            }

        status_info = []
        for port, data in SERVER_THREADS.items():
            if data.get("running", False):
                uptime = time.time() - data.get("start_time", time.time())
                connections = data.get("connections", 0)
                status_info.append(
                    f"Port {port}: Running - {connections} connections, uptime {uptime:.2f}s"
                )
            else:
                status_info.append(f"Port {port}: Stopped")

        return {
            "status": "success",
            "content": [
                {"text": "TCP Server Status:"},
                {"text": "\n".join(status_info)},
            ],
        }

    elif action == "client_send":
        host = host
        port = port
        message = message
        timeout = timeout
        buffer_size = buffer_size

        if not message:
            return {
                "status": "error",
                "content": [
                    {"text": "Error: No message provided for client_send action"}
                ],
            }

        # Create client socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(timeout)

        try:
            # Connect to server
            client_socket.connect((host, port))

            # Receive welcome message
            _welcome = client_socket.recv(buffer_size).decode()

            # Send message to server
            client_socket.sendall(message.encode())

            # Receive response
            response = client_socket.recv(buffer_size).decode()

            # Send exit message and close connection
            client_socket.sendall(b"exit")
            client_socket.close()

            return {
                "status": "success",
                "content": [
                    {"text": f"Connected to {host}:{port} successfully"},
                    {"text": f"Received welcome message: {_welcome}"},
                    {"text": f"Sent message: {message}"},
                    {"text": "Response received:"},
                    {"text": response},
                ],
            }

        except TimeoutError:
            return {
                "status": "error",
                "content": [
                    {
                        "text": f"Error: Connection to {host}:{port} timed out after {timeout} seconds"
                    }
                ],
            }
        except ConnectionRefusedError:
            return {
                "status": "error",
                "content": [
                    {
                        "text": f"Error: Connection to {host}:{port} refused - no server running on that port"
                    }
                ],
            }
        except Exception as e:
            return {
                "status": "error",
                "content": [{"text": f"Error connecting to {host}:{port}: {e!s}"}],
            }
        finally:
            try:
                client_socket.close()
            except OSError:
                # Socket already closed, safe to ignore
                pass

    else:
        return {
            "status": "error",
            "content": [
                {
                    "text": f"Error: Unknown action '{action}'. Supported actions are: "
                    f"start_server, stop_server, get_status, client_send"
                }
            ],
        }
