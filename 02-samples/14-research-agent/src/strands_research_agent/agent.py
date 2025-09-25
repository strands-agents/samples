#!/usr/bin/env python3
import time
import socket
import argparse
import base64
import os
import sys
import datetime
import json
import tempfile
import atexit
import shutil
from typing import Any
import uuid
from pathlib import Path

from strands import Agent
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
from strands.telemetry import StrandsTelemetry
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from strands_tools.utils.models.model import create_model
from strands_research_agent.handlers.callback_handler import callback_handler

hostname = socket.gethostname()
timestamp = str(int(time.time()))
instance_id = f"research-agent-{hostname}-{timestamp[-6:]}"

# Global secure temp directory - will be cleaned up on exit
_secure_temp_dir = None


def get_secure_temp_dir():
    """Get or create a secure temporary directory with proper permissions."""
    global _secure_temp_dir

    if _secure_temp_dir is None:
        # Create secure temporary directory with restrictive permissions (700)
        _secure_temp_dir = tempfile.mkdtemp(prefix="research_agent_", suffix="_secure")

        # Ensure only the current user can access it
        os.chmod(_secure_temp_dir, 0o700)

        # Register cleanup function to run on exit
        atexit.register(cleanup_temp_dir)

    return _secure_temp_dir


def cleanup_temp_dir():
    """Clean up the secure temporary directory on exit."""
    global _secure_temp_dir

    if _secure_temp_dir and os.path.exists(_secure_temp_dir):
        try:
            shutil.rmtree(_secure_temp_dir)
        except Exception as e:
            print(
                f"Warning: Could not clean up temporary directory {_secure_temp_dir}: {e}"
            )


def get_secure_research_dir():
    """Get secure research directory path within the temp directory."""
    secure_temp = get_secure_temp_dir()
    research_dir = Path(secure_temp) / ".research"

    # Create with secure permissions if it doesn't exist
    research_dir.mkdir(mode=0o700, exist_ok=True)

    return research_dir


def read_prompt_file():
    """Read system prompt text from .prompt file if it exists (repo or secure temp/.prompt)."""
    prompt_paths = [
        Path(".prompt"),
        get_secure_research_dir() / ".prompt",
        Path("README.md"),
    ]
    for path in prompt_paths:
        if path.is_file():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read(), str(path)
            except Exception:
                continue
    return "", None


def get_shell_history_file():
    """Get the research-specific history file path in secure temp directory."""
    secure_temp = get_secure_temp_dir()
    research_history = Path(secure_temp) / ".research_history"

    # Create with secure permissions if it doesn't exist
    if not research_history.exists():
        research_history.touch(mode=0o600)

    return str(research_history)


def get_shell_history_files():
    """Get available shell history file paths."""
    history_files = []

    # research history (primary) - now in secure temp directory
    research_history = Path(get_shell_history_file())
    if research_history.exists():
        history_files.append(("research", str(research_history)))

    # Bash history
    bash_history = Path.home() / ".bash_history"
    if bash_history.exists():
        history_files.append(("bash", str(bash_history)))

    # Zsh history
    zsh_history = Path.home() / ".zsh_history"
    if zsh_history.exists():
        history_files.append(("zsh", str(zsh_history)))

    return history_files


def extract_commands_from_history():
    """Extract commonly used commands from shell history for auto-completion."""
    commands = set()
    history_files = get_shell_history_files()

    # Limit the number of recent commands to process for performance
    max_recent_commands = 100

    for history_type, history_file in history_files:
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Take recent commands for better relevance
            recent_lines = (
                lines[-max_recent_commands:]
                if len(lines) > max_recent_commands
                else lines
            )

            for line in recent_lines:
                line = line.strip()
                if not line:
                    continue

                command = None

                if history_type == "research":
                    # Extract research commands
                    if "# research:" in line:
                        try:
                            query = line.split("# research:")[-1].strip()
                            # Extract first word as command
                            first_word = query.split()[0] if query.split() else None
                            if (
                                first_word and len(first_word) > 2
                            ):  # Only meaningful commands
                                commands.add(first_word.lower())
                        except (ValueError, IndexError):
                            continue

                elif history_type == "zsh":
                    # Zsh format: ": timestamp:0;command"
                    if line.startswith(": ") and ":0;" in line:
                        try:
                            parts = line.split(":0;", 1)
                            if len(parts) == 2:
                                full_command = parts[1].strip()
                                # Extract first word as command
                                first_word = (
                                    full_command.split()[0]
                                    if full_command.split()
                                    else None
                                )
                                if (
                                    first_word and len(first_word) > 1
                                ):  # Only meaningful commands
                                    commands.add(first_word.lower())
                        except (ValueError, IndexError):
                            continue

                elif history_type == "bash":
                    # Bash format: simple command per line
                    first_word = line.split()[0] if line.split() else None
                    if first_word and len(first_word) > 1:  # Only meaningful commands
                        commands.add(first_word.lower())

        except Exception as e:
            # Skip files that can't be read
            continue

    return list(commands)


def parse_history_line(line, history_type):
    """Parse a history line based on the shell type."""
    line = line.strip()
    if not line:
        return None

    if history_type == "research":
        # research format: ": timestamp:0;# research: query" or ": timestamp:0;# research_result: result"
        if "# research:" in line:
            try:
                timestamp_str = line.split(":")[1]
                timestamp = int(timestamp_str)
                readable_time = datetime.datetime.fromtimestamp(timestamp).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                query = line.split("# research:")[-1].strip()
                return ("you", readable_time, query)
            except (ValueError, IndexError):
                return None
        elif "# research_result:" in line:
            try:
                timestamp_str = line.split(":")[1]
                timestamp = int(timestamp_str)
                readable_time = datetime.datetime.fromtimestamp(timestamp).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                result = line.split("# research_result:")[-1].strip()
                return ("me", readable_time, result)
            except (ValueError, IndexError):
                return None

    elif history_type == "zsh":
        # Zsh format: ": timestamp:0;command"
        if line.startswith(": ") and ":0;" in line:
            try:
                parts = line.split(":0;", 1)
                if len(parts) == 2:
                    timestamp_str = parts[0].split(":")[1]
                    timestamp = int(timestamp_str)
                    readable_time = datetime.datetime.fromtimestamp(timestamp).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    command = parts[1].strip()
                    # Skip research commands to avoid duplication
                    if not command.startswith("research "):
                        return ("shell", readable_time, f"$ {command}")
            except (ValueError, IndexError):
                return None

    elif history_type == "bash":
        # Bash format: simple command per line (no timestamps usually)
        # We'll use a generic timestamp and only include recent ones
        readable_time = "recent"
        # Skip research commands to avoid duplication
        if not line.startswith("research "):
            return ("shell", readable_time, f"$ {line}")

    return None


def get_distributed_events(agent):
    """Get recent distributed events using the event_bridge tool."""
    try:
        # Check if event_bridge tool is available
        if not hasattr(agent.tool, "event_bridge"):
            return

        # Get distributed event count from environment variable, default to 25
        event_count = int(os.getenv("RESEARCH_DISTRIBUTED_EVENT_COUNT", "25"))

        # Subscribe to distributed events using the event_bridge tool
        agent.tool.event_bridge(action="subscribe", limit=event_count)

    except Exception as e:
        # Silently fail if distributed events can't be fetched
        return


def publish_conversation_turn(agent, query, response, event_type="conversation_turn"):
    """Publish a conversation turn to the distributed event bridge."""
    message_count = int(os.getenv("RESEARCH_LAST_MESSAGE_COUNT", "200"))

    try:
        # Check if event_bridge tool is available
        if not hasattr(agent.tool, "event_bridge"):
            return

        # Create a summary of the conversation turn
        response_summary = (
            str(response).replace("\n", " ")[:message_count] + "..."
            if len(str(response)) > message_count
            else str(response)
        )

        message = f"Q: {query}\nA: {response_summary}"

        # Publish the event using the event_bridge tool
        agent.tool.event_bridge(
            action="publish",
            message=message,
            event_type=event_type,
            record_direct_tool_call=False,
        )

    except Exception as e:
        # Silently fail if event publishing fails
        pass


def get_messages_dir():
    """Get the research messages directory path in secure temp directory."""
    messages_dir = get_secure_research_dir()
    return messages_dir


def get_session_file():
    """Get or create session file path in secure temp directory."""
    messages_dir = get_messages_dir()

    # Generate session ID based on date and UUID
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    session_id = str(uuid.uuid4())[:8]  # Short UUID

    session_file = messages_dir / f"{today}-{session_id}.json"
    return str(session_file)


def save_agent_messages(agent, session_file):
    """Save agent.messages to JSON file with secure permissions."""
    try:
        # Convert messages to serializable format
        messages_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "messages": [],
        }

        # Handle different message formats
        for msg in agent.messages:
            if hasattr(msg, "to_dict"):
                # If message has to_dict method
                messages_data["messages"].append(msg.to_dict())
            elif hasattr(msg, "__dict__"):
                # If message is an object with attributes
                msg_dict = {}
                for key, value in msg.__dict__.items():
                    try:
                        # Try to serialize the value
                        json.dumps(value)
                        msg_dict[key] = value
                    except (TypeError, ValueError):
                        # If not serializable, convert to string
                        msg_dict[key] = str(value)
                messages_data["messages"].append(msg_dict)
            else:
                # Fallback: convert to string
                messages_data["messages"].append(str(msg))

        # Write to file with secure permissions
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(messages_data, f, indent=2, ensure_ascii=False)

        # Ensure secure permissions
        os.chmod(session_file, 0o600)

    except Exception as e:
        # Silently fail if we can't save messages
        print(f"⚠️  Warning: Could not save messages: {e}")


def get_sqlite_memory_context(agent, user_query):
    """Get relevant context from SQLite memory based on user query."""
    try:
        if not hasattr(agent.tool, "sqlite_memory"):
            return ""

        # Search for relevant memories using full-text search
        result = agent.tool.sqlite_memory(
            action="search",
            query=user_query,
            search_type="fulltext",
            limit=5,
            record_direct_tool_call=False,
        )

        if "No memories found" in str(result):
            return ""

        # Extract and format context from memories
        context = "\n\n## 🧠 Relevant Memory Context:\n"
        context += (
            "Based on your query, here are relevant past conversations and knowledge:\n"
        )
        context += str(result) + "\n"

        return context
    except Exception as e:
        # Silently fail if memory search fails
        return ""


def get_retrieve_context(agent, user_query):
    """Get relevant context from Bedrock Knowledge Base using retrieve tool."""
    try:
        # Check if retrieve tool exists and knowledge base ID is available
        if not hasattr(agent.tool, "retrieve"):
            return ""

        knowledge_base_id = os.getenv("STRANDS_KNOWLEDGE_BASE_ID")
        if not knowledge_base_id:
            return ""

        # Retrieve relevant context from knowledge base
        result = agent.tool.retrieve(
            text=user_query,
            knowledgeBaseId=knowledge_base_id,
            numberOfResults=5,
            record_direct_tool_call=False,
        )

        if "No relevant content found" in str(result):
            return ""

        # Extract and format context from retrieved knowledge
        context = "\n\n## 📚 Retrieved Knowledge Base Context:\n"
        context += "Based on your query, here's relevant information from the knowledge base:\n"
        context += str(result) + "\n"

        return context
    except Exception as e:
        # Silently fail if knowledge retrieval fails
        return ""


def get_last_messages(agent=None, user_query=""):
    """Get the last N messages from multiple shell histories, distributed events, and SQLite memory for context."""
    try:
        # Get message count from environment variable, default to 200
        message_count = int(os.getenv("RESEARCH_LAST_MESSAGE_COUNT", "200"))

        all_entries = []

        # Get all history files (local shell history)
        history_files = get_shell_history_files()

        for history_type, history_file in history_files:
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                # For bash history, only take recent lines since there are no timestamps
                if history_type == "bash":
                    lines = lines[-message_count:]  # Only last N bash commands

                # Parse lines based on history type
                for line in lines:
                    parsed = parse_history_line(line, history_type)
                    if parsed:
                        all_entries.append(parsed)
            except Exception as e:
                # Skip files that can't be read
                continue

        # Get distributed events if agent is available
        if agent:
            try:
                get_distributed_events(agent)
            except Exception as e:
                # Skip distributed events if they can't be fetched
                pass

        # Take the last N entries
        recent_entries = (
            all_entries[-message_count:]
            if len(all_entries) >= message_count
            else all_entries
        )

        context = ""

        if recent_entries:
            # Format for context
            context += f"\n\nRecent conversation context (last {len(recent_entries)} messages):\n"
            for speaker, timestamp, content in recent_entries:
                context += f"[{timestamp}] {speaker}: {content}\n"

        # Add SQLite memory context if user query is provided
        if agent and user_query:
            memory_context = get_sqlite_memory_context(agent, user_query)
            context += memory_context

            # Add retrieve context from knowledge base if available
            retrieve_context = get_retrieve_context(agent, user_query)
            context += retrieve_context

        return context

    except Exception:
        return ""


def store_conversation_in_sqlite_memory(agent, query, result):
    """Store conversation turn in SQLite memory for future retrieval."""
    try:
        if not hasattr(agent.tool, "sqlite_memory"):
            return

        # Create conversation content by combining user input and agent result
        conversation_content = f"User Query: {query}\n\nAgent Response: {str(result)}"

        # Create title with research prefix, current date, and user query (truncated)
        query_preview = query[:50] + "..." if len(query) > 50 else query
        conversation_title = f"Research Conversation: {datetime.datetime.now().strftime('%Y-%m-%d')} | {query_preview}"

        # Store in SQLite memory with relevant tags
        agent.tool.sqlite_memory(
            action="store",
            content=conversation_content,
            title=conversation_title,
            tags=["conversation", "research", "user_interaction"],
            metadata={
                "query_length": len(query),
                "response_length": len(str(result)),
                "timestamp": datetime.datetime.now().isoformat(),
                "session_id": instance_id,
            },
            record_direct_tool_call=False,
        )
    except Exception as e:
        # Silently fail if storage fails
        pass


def store_conversation_in_kb(agent, query, result):
    """Store conversation turn in Bedrock Knowledge Base for future retrieval."""
    try:
        # Check if store_in_kb tool exists and knowledge base ID is available
        if not hasattr(agent.tool, "store_in_kb"):
            return

        knowledge_base_id = os.getenv("STRANDS_KNOWLEDGE_BASE_ID")
        if not knowledge_base_id:
            return

        # Create conversation content by combining user input and agent result
        conversation_content = f"User Query: {query}\n\nAgent Response: {str(result)}"

        # Create title with research prefix, current date, and user query (truncated)
        query_preview = query[:50] + "..." if len(query) > 50 else query
        conversation_title = f"research Conversation: {datetime.datetime.now().strftime('%Y-%m-%d')} | {query_preview}"

        # Store in knowledge base
        agent.tool.store_in_kb(
            content=conversation_content,
            title=conversation_title,
            knowledge_base_id=knowledge_base_id,
            record_direct_tool_call=False,
        )
    except Exception as e:
        # Silently fail if knowledge base storage fails
        pass


def append_to_shell_history(query, response):
    """Append the interaction to research shell history in secure temp directory."""
    try:
        history_file = get_shell_history_file()

        # Format the entry for shell history
        # Use a comment format that's shell-compatible
        # Use a more secure way to get timestamp instead of shell command
        timestamp = str(int(time.time()))

        with open(history_file, "a", encoding="utf-8") as f:
            # Add the query
            f.write(f": {timestamp}:0;# research: {query}\n")
            # Add a compressed version of the response
            response_summary = (
                str(response).replace("\n", " ")[
                    : int(os.getenv("RESEARCH_RESPONSE_SUMMARY_LENGTH", "10000"))
                ]
                + "..."
            )
            f.write(f": {timestamp}:0;# research_result: {response_summary}\n")

        # Ensure secure permissions
        os.chmod(history_file, 0o600)

    except Exception as e:
        # Silently fail if we can't write to history
        pass


def setup_otel() -> None:
    """Setup OpenTelemetry if configured."""
    otel_host = os.environ.get("LANGFUSE_HOST")

    if otel_host:
        public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
        secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")

        if public_key and secret_key:
            auth_token = base64.b64encode(
                f"{public_key}:{secret_key}".encode()
            ).decode()
            otel_endpoint = f"{otel_host}/api/public/otel"

            os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = os.environ.get(
                "OTEL_EXPORTER_OTLP_ENDPOINT", otel_endpoint
            )
            os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = os.environ.get(
                "OTEL_EXPORTER_OTLP_HEADERS", f"Authorization=Basic {auth_token}"
            )

            strands_telemetry = StrandsTelemetry()
            strands_telemetry.setup_otlp_exporter()


def get_tools() -> dict[str, Any]:
    """Returns the filtered collection of available agent tools for strands.

    This function first gets all available tools, then filters them based on
    the STRANDS_TOOLS environment variable if it exists.

    Returns:
        Dict[str, Any]: Dictionary mapping tool names to tool functions
    """
    # First get all tools
    tools = _get_all_tools()

    # Then apply filtering based on environment variable
    return _filter_tools(tools)


def _get_all_tools() -> dict[str, Any]:
    """Returns all available tools without filtering.

    Returns:
        Dict[str, Any]: Dictionary mapping tool names to tool functions
    """
    tools = {}

    try:
        # Strands tools
        from strands_research_agent.tools import (
            event_bridge,
            tcp,
            scraper,
            tasks,
            dialog,
            graphql,
            use_github,
            fetch_github_tool,
            s3_memory,
            listen,
            sqlite_memory,
            store_in_kb,
            system_prompt,
            notify,
        )

        from strands_tools import (
            python_repl,
            calculator,
            current_time,
            editor,
            environment,
            file_read,
            file_write,
            generate_image,
            http_request,
            image_reader,
            journal,
            diagram,
            mcp_client,
            load_tool,
            memory,
            nova_reels,
            retrieve,
            slack,
            speak,
            shell,
            stop,
            swarm,
            think,
            use_aws,
            workflow,
            use_agent,
        )

        tools = {
            "listen": listen,
            "notify": notify,
            "store_in_kb": store_in_kb,
            "graphql": graphql,
            "use_github": use_github,
            "fetch_github_tool": fetch_github_tool,
            "event_bridge": event_bridge,
            "tcp": tcp,
            "use_agent": use_agent,
            "shell": shell,
            "scraper": scraper,
            "tasks": tasks,
            "environment": environment,
            "dialog": dialog,
            "mcp_client": mcp_client,
            "python_repl": python_repl,
            "calculator": calculator,
            "current_time": current_time,
            "editor": editor,
            "file_read": file_read,
            "file_write": file_write,
            "generate_image": generate_image,
            "http_request": http_request,
            "image_reader": image_reader,
            "journal": journal,
            "diagram": diagram,
            "load_tool": load_tool,
            "system_prompt": system_prompt,
            "s3_memory": s3_memory,
            "sqlite_memory": sqlite_memory,
            "memory": memory,
            "nova_reels": nova_reels,
            "retrieve": retrieve,
            "slack": slack,
            "speak": speak,
            "stop": stop,
            "swarm": swarm,
            "think": think,
            "use_aws": use_aws,
            "workflow": workflow,
        }

    except ImportError as e:
        print(f"Warning: Could not import all tools: {e!s}")

    return tools


def _filter_tools(all_tools: dict[str, Any]) -> dict[str, Any]:
    """Filter tools based on RESEARCH_STRANDS_TOOLS environment variable.

    Supports both comma-separated strings and JSON arrays for flexibility.

    Args:
        all_tools: Dictionary of all available tools

    Returns:
        Dict[str, Any]: Filtered dictionary of tools
    """
    # Get tool filter from environment variable
    tool_filter_str = os.getenv("RESEARCH_STRANDS_TOOLS", "ALL")

    # If env var not set or set to 'ALL', return all tools
    if not tool_filter_str or tool_filter_str == "ALL":
        return all_tools

    tool_filter = None

    # First try to parse as JSON array
    try:
        tool_filter = json.loads(tool_filter_str)
        if not isinstance(tool_filter, list):
            tool_filter = None
    except json.JSONDecodeError:
        # If JSON parsing fails, try comma-separated string
        pass

    # If JSON parsing failed or didn't produce a list, try comma-separated
    if tool_filter is None:
        # Handle comma-separated string format
        tool_filter = [
            tool.strip() for tool in tool_filter_str.split(",") if tool.strip()
        ]

        # If we still don't have a valid list, return all tools
        if not tool_filter:
            print(
                "Warning: RESEARCH_STRANDS_TOOLS env var is not a valid JSON array or comma-separated string. Using all tools."
            )
            return all_tools

    # Filter the tools
    filtered_tools = {}
    for tool_name in tool_filter:
        if tool_name in all_tools:
            filtered_tools[tool_name] = all_tools[tool_name]
        else:
            print(
                f"Warning: Tool '{tool_name}' specified in RESEARCH_STRANDS_TOOLS env var not found."
            )

    return filtered_tools


def create_agent(model_provider="bedrock"):
    """
    Create a Strands Agent with MCP integration.

    Args:
        model_provider: Model provider, default bedrock (default: sonnet-4)

    Returns:
        tuple: (Agent, MCPClient) - Agent and MCP client to keep context alive
    """
    setup_otel()

    model = create_model(provider=os.getenv("MODEL_PROVIDER", model_provider))

    tools = get_tools()

    stdio_mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="uvx",
                args=["strands-agents-mcp-server"],
            )
        )
    )

    # Get MCP tools (outside context for now)
    try:
        with stdio_mcp_client:
            mcp_tools = stdio_mcp_client.list_tools_sync()
    except Exception as e:
        print(f"⚠️  Warning: Could not load MCP tools: {e}")
        mcp_tools = []

    # Create the agent with combined tools
    agent = Agent(
        model=model,
        tools=list(tools.values()) + mcp_tools,
        callback_handler=callback_handler,
        load_tools_from_directory=True,
        trace_attributes={
            "session.id": instance_id,
            "user.id": "strands-agent@users.noreply.github.com",
            "tags": [
                "Strands-Agents",
            ],
        },
    )

    # Return both agent and MCP client
    return agent, stdio_mcp_client


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="research",
        description="strands research agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  research                              # Interactive mode
  research hello world                  # Single query mode
  research "what can you do"            # Single query with quotes
  research "hello world" --interactive  # Query then stay interactive
  research --version                    # Show version information
        """,
    )

    parser.add_argument(
        "query",
        nargs="*",
        help="Query to ask the agent (if provided, runs once and exits unless --interactive is used)",
    )

    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Keep the conversation active after processing the initial query (useful in tmux)",
    )

    parser.add_argument(
        "--no-update-check",
        action="store_true",
        help="Skip checking for updates on startup",
    )

    return parser.parse_args()


def main():
    """Main entry point for the research agent."""
    # Parse command line arguments
    args = parse_args()

    # Show configuration
    model_provider = os.getenv("MODEL_PROVIDER", "bedrock")

    # Create agent first (needed for distributed events)
    agent, mcp_client = create_agent(model_provider)

    # Use MCP client context manager to keep MCP tools alive
    with mcp_client:
        # Get recent conversation context (including distributed events and SQLite memory)
        recent_context = get_last_messages(agent)

        # Enhanced system prompt with history context and self-modification instructions
        base_prompt = "i'm research agent. minimalist agent. welcome to chat."
        # Read .prompt or secure temp/.prompt if present
        prompt_file_content, prompt_file_path = read_prompt_file()
        if prompt_file_content and prompt_file_path:
            prompt_file_note = f"\n\n[Loaded system prompt from: {prompt_file_path}]\n{prompt_file_content}\n"
        else:
            prompt_file_note = ""

        # Runtime and Environment Information
        runtime_info = f"""

## 🚀 Runtime Environment:
- **Current Directory:** {Path.cwd()}
- **Python Version:** {sys.version.split()[0]}
- **Platform:** {os.name} ({sys.platform})
- **User:** {os.getenv('USER', 'unknown')}
- **Hostname:** {socket.gethostname()}
- **Session ID:** {instance_id}
- **Timestamp:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Secure Temp Directory:** {get_secure_temp_dir()}

## 📚 Knowledge Base Integration:
- **Dual storage** - Conversations stored in both SQLite memory and knowledge base
- **Context awareness** - Agent has access to historical conversations and knowledge

**Note:** Tool availability depends on RESEARCH_STRANDS_TOOLS environment variable. Current filter: {os.getenv('RESEARCH_STRANDS_TOOLS', 'ALL')}

## Tool Creation & Hot Reload System:
### **CRITICAL: You have FULL tool creation capabilities enabled!**

**🔧 Hot Reload System Active:**
- **Instant Tool Creation** - Save any .py file in `./tools/` and it becomes immediately available
- **No Restart Needed** - Tools are auto-loaded and ready to use instantly
- **Live Development** - Modify existing tools while running and test immediately
- **Full Python Access** - Create any Python functionality as a tool

**🛠️ Tool Creation Patterns:**

### **1. Simple @tool Decorator (Recommended):**
```python
# ./tools/my_tool.py
from strands import tool

@tool
def calculate_tip(amount: float, percentage: float = 15.0) -> str:
    \"\"\"Calculate tip and total for a bill.
    
    Args:
        amount: Bill amount in dollars
        percentage: Tip percentage (default: 15.0)
        
    Returns:
        str: Formatted tip calculation result
    \"\"\"
    tip = amount * (percentage / 100)
    total = amount + tip
    return f"Tip: tip:.2f, Total: total:.2f"
```

### **2. Advanced Action-Based Pattern:**
```python
# ./tools/weather.py
from typing import Dict, Any
from strands import tool

@tool
def weather_tool(action: str, location: str = None, **kwargs) -> Dict[str, Any]:
    \"\"\"Comprehensive weather information tool.
    
    Args:
        action: Action to perform (current, forecast, alerts)
        location: City name (required)
        **kwargs: Additional parameters
        
    Returns:
        Dict containing status and response content
    \"\"\"
    if action == "current":
        return "status": "success", "content": "text": f"Weather for location"
    elif action == "forecast":
        return "status": "success", "content": "text": f"Forecast for location"
    else:
        return "status": "error", "content": "text": f"Unknown action: action"
```

**Response Format:**
- Tool calls: **MAXIMUM PARALLELISM - ALWAYS** 
- Communication: **MINIMAL WORDS**
- Efficiency: **Speed is paramount**
"""
        self_modify_note = (
            "\n\nNote: The system prompt for research is built from your base instructions, "
            "conversation history, and the .prompt file (in this directory or secure temp/.prompt). "
            "You can modify the system prompt in multiple ways:\n"
            "1. **Edit .prompt file** - Create/modify .prompt in current directory or secure temp/.prompt\n"
            "2. **SYSTEM_PROMPT environment variable** - Set SYSTEM_PROMPT env var to extend the system prompt\n"
            "3. **Environment tool** - Use environment(action='set', name='SYSTEM_PROMPT', value='additional text')\n"
            "4. **Runtime modification** - The SYSTEM_PROMPT env var is appended to every system prompt automatically"
        )

        system_prompt = (
            base_prompt
            + recent_context
            + prompt_file_note
            + runtime_info
            + self_modify_note
            # add own codebase fs read here - should work even in package shared and downloaded over pypi or pipx
            + os.getenv("SYSTEM_PROMPT", ".")
        )

        # Set system prompt
        agent.system_prompt = system_prompt

        # Get session file for storing messages
        session_file = get_session_file()
        print(f"📝 Session messages will be saved to: {session_file}")

        # Check if query provided as arguments
        if args.query:
            # Single query mode - join all arguments as the query
            query = " ".join(args.query)
            print(f"\n# {query}")

            try:
                result = agent(query)
                append_to_shell_history(query, result)
                save_agent_messages(agent, session_file)
                # Store conversation in SQLite memory for future context retrieval
                store_conversation_in_sqlite_memory(agent, query, result)
                # Store conversation in knowledge base if available
                store_conversation_in_kb(agent, query, result)
                # Store conversation in knowledge base if kb exists and store_in_kb exists
                # Publish conversation turn to distributed event bridge
                publish_conversation_turn(agent, query, result)
            except Exception as e:
                print(f"❌ Error: {e}")
                sys.exit(1)

            # If --interactive flag is set, continue to interactive mode
            if not args.interactive:
                return

        print("💡 Type 'exit', 'quit', or 'bye' to quit, or Ctrl+C")

        # Set up prompt_toolkit with history in secure temp directory
        history_file = get_shell_history_file()
        history = FileHistory(history_file)

        # Create completions from common commands and shell history
        base_commands = ["exit", "quit", "bye", "help", "clear", "ls", "pwd", "cd"]
        history_commands = extract_commands_from_history()

        # Combine base commands with commands from history
        all_commands = list(set(base_commands + history_commands))
        completer = WordCompleter(all_commands, ignore_case=True)

        while True:
            try:
                # Use prompt_toolkit for enhanced input
                q = prompt(
                    "\n# ",
                    history=history,
                    auto_suggest=AutoSuggestFromHistory(),
                    completer=completer,
                    complete_while_typing=True,
                    mouse_support=False,  # breaks scrolling when enabled
                )

                if q.startswith("!"):
                    shell_command = q[1:]  # Remove the ! prefix
                    try:
                        result = agent.tool.shell(command=shell_command, timeout=900)
                        append_to_shell_history(q, result["content"][0]["text"])
                        save_agent_messages(agent, session_file)
                        # Store shell command in SQLite memory for future reference
                        store_conversation_in_sqlite_memory(
                            agent, q, result["content"][0]["text"]
                        )
                        # Store shell command in knowledge base if available
                        store_conversation_in_kb(agent, q, result["content"][0]["text"])
                        # Publish shell command to distributed event bridge
                        publish_conversation_turn(
                            agent, q, result["content"][0]["text"], "shell_command"
                        )
                    except Exception as e:
                        print(f"Shell command execution error: {str(e)}")
                    continue

                if q.lower() in ["exit", "quit", "bye"]:
                    print("\n👋 Goodbye!")
                    break

                if not q.strip():
                    continue

                # Get recent conversation context (including distributed events and SQLite memory)
                recent_context = get_last_messages(agent, q)

                # Enhanced system prompt with history context and self-modification instructions
                base_prompt = "i'm research. minimalist agent. welcome to chat."
                # Read .prompt or secure temp/.prompt if present
                prompt_file_content, prompt_file_path = read_prompt_file()
                if prompt_file_content and prompt_file_path:
                    prompt_file_note = f"\n\n[Loaded system prompt from: {prompt_file_path}]\n{prompt_file_content}\n"
                else:
                    prompt_file_note = ""

                self_modify_note = (
                    "\n\nNote: The system prompt for research is built from your base instructions, "
                    "conversation history, and the .prompt file (in this directory or secure temp/.prompt). "
                    "You can modify the system prompt in multiple ways:\n"
                    "1. **Edit .prompt file** - Create/modify .prompt in current directory or secure temp/.prompt\n"
                    "2. **SYSTEM_PROMPT environment variable** - Set SYSTEM_PROMPT env var to extend the system prompt\n"
                    "3. **Environment tool** - Use environment(action='set', name='SYSTEM_PROMPT', value='additional text')\n"
                    "4. **Runtime modification** - The SYSTEM_PROMPT env var is appended to every system prompt automatically"
                )

                system_prompt = (
                    base_prompt
                    + recent_context
                    + prompt_file_note
                    + runtime_info
                    + self_modify_note
                    + os.getenv("SYSTEM_PROMPT", ".")
                )
                agent.system_prompt = system_prompt

                result = agent(q)

                append_to_shell_history(q, result)
                save_agent_messages(agent, session_file)
                # Store conversation in SQLite memory for future context retrieval
                store_conversation_in_sqlite_memory(agent, q, result)
                # Store conversation in knowledge base if available
                store_conversation_in_kb(agent, q, result)
                # Publish conversation turn to distributed event bridge
                publish_conversation_turn(agent, q, result)

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                continue


if __name__ == "__main__":
    main()
