"""
AI Triage Agent - Backend
Real Strands Agent integration with MCP servers
"""

import os
import json
import logging
import asyncio
import time
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dataclasses import dataclass, asdict, field
import re

# Strands imports
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from mcp import StdioServerParameters, stdio_client
from mcpmanager import mcp_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store server logs
server_logs: Dict[str, List[str]] = {}
mcp_servers = {}  # Initialize early to avoid loading issues
mcp_clients = {}  # Store MCP client instances

def add_server_log(server_name: str, message: str, level: str = "info", details: Dict = None):
    """Add a structured log entry for a server"""
    timestamp = datetime.now().isoformat()
    
    # Create structured log entry
    log_entry = {
        "timestamp": timestamp,
        "server": server_name,
        "level": level,
        "message": message,
        "details": details or {}
    }
    
    if server_name not in server_logs:
        server_logs[server_name] = []
    
    # Prevent duplicate consecutive messages (but allow tool executions)
    if server_logs[server_name] and not message.startswith("Executing "):
        last_log = server_logs[server_name][-1]
        if isinstance(last_log, dict) and last_log.get("message") == message:
            return  # Skip duplicate message
    
    server_logs[server_name].append(log_entry)
    
    # Keep only last 50 logs per server
    if len(server_logs[server_name]) > 50:
        server_logs[server_name] = server_logs[server_name][-50:]

# Global agent cache - session-based
session_agents = {}

# Global tools cache
cached_tools = []
tools_last_updated = None

# Session token tracking
session_token_usage = {}  # session_id -> {"total_input": int, "total_output": int}

# Global decision tree instance
decision_tree = None

# --- Start of Inlined Decision Tree Logic ---

@dataclass
class DecisionNode:
    """Represents a single node in the decision tree"""
    id: str
    topic: str
    question: str
    ui_display: str
    response_options: List[str]
    should_reason: bool
    reasoning_rules: str
    additional_reasoning: str
    required: bool = True
    dependencies: List[str] = None
    children: List[str] = None
    is_terminal: bool = False
    outcome: Optional[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.children is None:
            self.children = []

@dataclass
class ConversationState:
    """Tracks the state of a user's conversation through the decision tree"""
    session_id: str
    current_node_id: str
    user_responses: Dict[str, str] = field(default_factory=dict)
    reasoning_trail: List[str] = field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    chat_mode: bool = False
    completed: bool = False
    outcome: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    last_user_input: str = ""

class DecisionTree:
    """Manages the decision tree logic and conversation states, self-contained within main.py."""
    
    def __init__(self, data_file: str):
        self.nodes: Dict[str, DecisionNode] = {}
        self.conversations: Dict[str, ConversationState] = {}
        self.data_file = data_file
        self.load_data()
    
    def load_data(self):
        """Load decision tree data from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            for node_id, node_data in data['nodes'].items():
                self.nodes[node_id] = DecisionNode(**node_data)
            
            logger.info(f"Loaded {len(self.nodes)} decision tree nodes")
        except Exception as e:
            logger.error(f"Failed to load decision tree data: {e}")
            raise

    def start_session(self, session_id: str, chat_mode: bool = False) -> None:
        """Start a new decision tree session."""
        if session_id in self.conversations:
            return

        self.conversations[session_id] = ConversationState(
            session_id=session_id,
            current_node_id="start",
            chat_mode=chat_mode
        )
        logger.info(f"Started new session {session_id} in chat_mode={chat_mode}")

    def set_current_node(self, session_id: str, node_id: str) -> bool:
        """Forcefully set the current node for a session."""
        if session_id in self.conversations and node_id in self.nodes:
            old_node = self.conversations[session_id].current_node_id
            self.conversations[session_id].current_node_id = node_id
            self.conversations[session_id].last_updated = datetime.now()
            logger.info(f"Session {session_id} current node manually set to {node_id}")
            add_server_log("triage", f"NODE TRANSITION: {session_id} - {old_node} -> {node_id}", level="info", details={
                "session_id": session_id,
                "old_node": old_node,
                "new_node": node_id,
                "timestamp": datetime.now().isoformat()
            })
            return True
        logger.warning(f"Failed to set node for session {session_id} to {node_id}. Session or node not found.")
        add_server_log("triage", f"NODE TRANSITION FAILED: {session_id} - target: {node_id}", level="warning", details={
            "session_id": session_id,
            "target_node": node_id,
            "session_exists": session_id in self.conversations,
            "node_exists": node_id in self.nodes
        })
        return False

# --- End of Inlined Decision Tree Logic ---

def refresh_tools_cache():
    """Refresh the global tools cache"""
    global cached_tools, tools_last_updated
    
    try:
        cached_tools = mcp_manager.get_all_tools(active_only=True)
        tools_last_updated = datetime.now()
        add_server_log("system", f"Tools cache refreshed: {len(cached_tools)} tools loaded", level="info", details={"tool_count": len(cached_tools)})
    except Exception as e:
        add_server_log("system", f"Error refreshing tools cache: {str(e)}", level="error", details={"error": str(e)})
        cached_tools = []

def get_cached_tools():
    """Get cached tools, refresh if empty"""
    global cached_tools
    
    if not cached_tools:
        refresh_tools_cache()
    
    return cached_tools

# Initialize MCP manager after function definitions
mcp_manager.initialize_default_clients()
add_server_log("system", f"MCP Manager initialized with clients: {mcp_manager.get_active_clients()}", level="info", details={"active_clients": mcp_manager.get_active_clients()})

# Pre-load tools cache
refresh_tools_cache()

def get_or_create_session_agent(session_id: str, model_id: str) -> Agent:
    """Get or create a cached agent for the given session and model"""
    agent_key = f"{session_id}:{model_id}"
    
    if agent_key not in session_agents:
        model = BedrockModel(model_id=model_id, temperature=0.7)
        tools = get_cached_tools()
        
        # General purpose prompt. Specific instructions will be provided in each call.
        system_prompt = """You are a helpful and empathetic AI Triage Assistant.
Your goal is to guide users through a structured assessment.
You must follow the specific instructions given in each prompt precisely.
Always provide your response in a clear, conversational, and professional manner.
The user-facing response must NOT include any system commands or XML tags unless specifically requested.

FORMATTING GUIDELINES:
- Use **bold text** for important questions, warnings, or key medical information
- Use clear, conversational language that patients can easily understand
- Highlight urgent situations with appropriate emphasis
- Make important medical advice stand out visually
"""
        
        agent = Agent(model=model, system_prompt=system_prompt, tools=tools)
        session_agents[agent_key] = agent
        add_server_log("system", f"Session agent cached for {session_id}:{model_id}")
    
    return session_agents[agent_key]

def get_session_messages_for_ui(session_id: str, model_id: str) -> List[Dict]:
    """Get session messages formatted for UI from the actual agent"""
    agent_key = f"{session_id}:{model_id}"
    
    if agent_key not in session_agents:
        return []
    
    agent = session_agents[agent_key]
    
    # Get messages from agent.messages
    if not hasattr(agent, 'messages') or not agent.messages:
        return []
    
    ui_messages = []
    
    for msg in agent.messages:
        # Skip system messages
        if msg.get('role') == 'system':
            continue
            
        # Convert Strands message format to UI format
        if msg.get('role') in ['user', 'assistant']:
            message_content = ""
            
            # Extract content from Strands message format
            content = msg.get('content', [])
            if isinstance(content, str):
                message_content = content
            elif isinstance(content, list):
                text_parts = []
                for content_item in content:
                    if isinstance(content_item, dict):
                        if 'text' in content_item:
                            text_parts.append(content_item['text'])
                        elif 'toolUse' in content_item:
                            tool_use = content_item['toolUse']
                            text_parts.append(f"🔧 Used tool: {tool_use.get('name', 'unknown')}")
                        elif 'toolResult' in content_item:
                            tool_result = content_item['toolResult']
                            if 'content' in tool_result and tool_result['content']:
                                result_text = tool_result['content'][0].get('text', '') if tool_result['content'] else ''
                                text_parts.append(f"✅ Result: {result_text[:100]}...")
                    else:
                        text_parts.append(str(content_item))
                message_content = "\n".join(text_parts)
            
            ui_messages.append({
                "id": len(ui_messages) + 1,
                "role": msg['role'],
                "content": message_content,
                "timestamp": datetime.now().isoformat(),  # We don't have original timestamp
                "model": model_id if msg['role'] == 'assistant' else None
            })
    
    return ui_messages

def refresh_agents():
    """Refresh tools cache and clear agent cache"""
    global session_agents
    
    # Refresh tools cache first
    refresh_tools_cache()
    
    # Clear agent cache so they get recreated with new tools
    session_agents.clear()
    add_server_log("system", "Tools and agent cache refreshed - agents will recreate with new tools", level="info", details={"cleared_sessions": len(session_agents)})

def load_mcp_config():
    """Load MCP configuration from mcp.json file"""
    global mcp_servers
    if mcp_servers:  # Already loaded
        return mcp_servers
        
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'mcp.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        # Transform config to our internal format
        mcp_servers = {}
        
        # Check for both 'servers' and 'mcpServers' keys for compatibility
        servers_config = config.get('mcpServers', config.get('servers', {}))
        
        for server_name, server_config in servers_config.items():
            mcp_servers[server_name] = {
                "name": server_config.get("name", server_name.replace('_', ' ').title()),
                "enabled": server_config.get("enabled", True),
                "description": server_config.get("description", f"{server_name.replace('_', ' ').title()} MCP server"),
                "status": "ready" if server_config.get("enabled", True) else "disabled",
                "command": server_config.get("command", ""),
                "args": server_config.get("args", []),
                "env": server_config.get("env", {})
            }
        
        add_server_log("system", f"Loaded {len(mcp_servers)} MCP servers")
        return mcp_servers
        
    except Exception as e:
        logger.error(f"Error loading MCP config: {e}")
        add_server_log("system", f"Error loading MCP config: {e}")
        return {}

def save_mcp_config(servers_config):
    """Save MCP configuration to mcp.json file"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'mcp.json')
        
        # Load existing config
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Get the correct servers key
        servers_key = 'mcpServers' if 'mcpServers' in config else 'servers'
        
        # Update server enabled states
        for server_name, server_info in servers_config.items():
            if server_name in config.get(servers_key, {}):
                config[servers_key][server_name]['enabled'] = server_info.get('enabled', True)
        
        # Save updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
            
        add_server_log("system", "Configuration saved")
        
    except Exception as e:
        logger.error(f"Error saving MCP config: {e}")
        add_server_log("system", f"Error saving config: {e}")

def estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation: ~4 chars per token)"""
    if not text:
        return 0
    # Simple and conservative estimation: 4 characters per token
    return max(1, len(text) // 4)

def setup_mcp_servers():
    """Setup MCP servers using stdio transport"""
    global mcp_clients
    
    for server_name, server_config in mcp_servers.items():
        if not server_config.get("enabled", True):
            add_server_log(server_name, "Server disabled, skipping")
            continue
            
        try:
            # Prepare command - find available python commandㅂ
            def find_python_command():
                import shutil
                if shutil.which("python"):
                    return "python"
                elif shutil.which("python3"):
                    return "python3"
                else:
                    return "python"  # fallback
            
            default_python = find_python_command()
            command = server_config.get("command", default_python)
            args = server_config.get("args", [])
            
            # Build full command
            full_command = [command] + args
            
            add_server_log(server_name, f"Setting up MCP server: {' '.join(full_command)}")
            
            # Create MCP Client for stdio transport (similar to the example)
            mcp_client = MCPClient(
                lambda: stdio_client(
                    StdioServerParameters(
                        command=command,
                        args=args,
                        cwd=os.path.dirname(__file__)
                    )
                )
            )
            
            mcp_clients[server_name] = mcp_client
            mcp_servers[server_name]["status"] = "ready"
            add_server_log(server_name, "MCP server ready")
                
        except Exception as e:
            add_server_log(server_name, f"Setup error: {str(e)}")
            mcp_servers[server_name]["status"] = "error"

def get_all_mcp_tools():
    """Get all tools from MCP servers"""
    all_tools = []
    
    for server_name, mcp_client in mcp_clients.items():
        try:
            # Note: We don't use 'with' here as tools are used later in the agent
            # The agent will handle the context when it uses the tools
            tools = mcp_client.list_tools_sync()
            if tools:
                all_tools.extend(tools)
                add_server_log(server_name, f"Loaded {len(tools)} tools")
        except Exception as e:
            add_server_log(server_name, f"Tool loading error: {str(e)}")
    
    return all_tools

# Available models with new Claude versions
AVAILABLE_MODELS = [
    {
        "id": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "name": "Claude 3.7 Sonnet",
        "description": "Latest version with enhanced capabilities"
    },
    {
        "id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        "name": "Claude 3.5 Sonnet",
        "description": "Advanced reasoning and analysis"
    },
    {
        "id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
        "name": "Claude Sonnet 4",
        "description": "Most advanced Claude model with superior reasoning"
    },
    {
        "id": "anthropic.claude-3-haiku-20240307-v1:0",
        "name": "Claude 3 Haiku",
        "description": "Fast and efficient responses"
    },
    {
        "id": "us.amazon.nova-pro-v1:0",
        "name": "Amazon Nova Pro",
        "description": "High-performance multimodal model"
    },
    {
        "id": "us.amazon.nova-lite-v1:0",
        "name": "Amazon Nova Lite",
        "description": "Balanced performance and cost-effectiveness"
    },
    {
        "id": "us.amazon.nova-micro-v1:0",
        "name": "Amazon Nova Micro", 
        "description": "Lightweight model for simple tasks"
    }
]

# Initialize Strands Agents for different models
agents_cache = {}

def create_mcp_agent_tools():
    """Create MCP tools that can be used by the agent"""
    from strands import tool
    
    mcp_tools = []
    
    for server_name, mcp_client in mcp_clients.items():
        if not mcp_servers[server_name].get("enabled", True):
            continue
            
        # Create a tool function for each MCP server
        @tool
        def mcp_server_tool(query: str, server_name=server_name, client=mcp_client) -> str:
            f"""
            Interact with {server_name} MCP server

            Args:
                query: The user's query or command

            Returns:
                Response from the MCP server
            """
            try:
                with client:
                    tools = client.list_tools_sync()
                    if tools:
                        # For now, we'll use the first available tool
                        # In a real implementation, you'd parse the query and select the appropriate tool
                        return f"MCP server {server_name} has {len(tools)} available tools"
                    else:
                        return f"No tools available on {server_name} server"
            except Exception as e:
                return f"Error accessing {server_name} server: {str(e)}"
        
        # Set the tool name dynamically
        mcp_server_tool.__name__ = f"{server_name}_tool"
        mcp_tools.append(mcp_server_tool)
    
    return mcp_tools

def get_strands_agent(model_id: str):
    """Get or create a Strands agent for the specified model"""
    try:
        add_server_log("system", f"Creating agent for {model_id}")
        
        # Create Bedrock model instance
        bedrock_model = BedrockModel(
            model_id=model_id,
            region_name=os.environ.get('AWS_REGION', 'us-east-1'),
            temperature=0.7,
        )
        
        # Get MCP tools
        mcp_tools = create_mcp_agent_tools()
        
        # Create agent with MCP tools integration
        system_prompt = f"""You are a helpful AI assistant for AI Triage Agent. 
You have access to various tools and services through MCP servers.

Available MCP servers: {len(mcp_clients)} servers

Always provide clear, accurate, and helpful responses in markdown format when appropriate.
Use the available tools when relevant to answer user questions. Analyze the user's request
and determine which tools would be most helpful to provide a complete response."""
        
        agent = Agent(
            model=bedrock_model,
            system_prompt=system_prompt,
            tools=mcp_tools if mcp_tools else None
        )
        
        add_server_log("system", f"Agent ready with {len(mcp_tools)} MCP tools: {model_id}")
        return agent
        
    except Exception as e:
        logger.error(f"Error creating Strands agent for {model_id}: {e}")
        add_server_log("system", f"Agent error: {str(e)[:50]}...")
        raise

# Load MCP servers from configuration at startup
load_mcp_config()

def initialize_mcp_servers():
    """Initialize all MCP servers"""
    add_server_log("system", "Initializing MCP servers...")
    
    # Setup MCP servers
    setup_mcp_servers()
    
    add_server_log("system", "MCP initialization complete")

# FastAPI app setup
app = FastAPI(title="AI Triage Agent API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ImageData(BaseModel):
    data: str  # base64 encoded image data
    name: str  # filename

class ChatMessage(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    message: str
    model_id: Optional[str] = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    session_id: Optional[str] = "default"
    images: Optional[List[ImageData]] = None
    history: Optional[List[Dict[str, Any]]] = None

class ChatResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    response: str
    model_id: str
    tokens: Dict[str, int]

async def stream_plain_text_response_generator(text: str, model_id: str, tokens: Dict[str, int]):
    """An async generator to stream a plain text response chunk by chunk."""
    # Stream back the response word by word
    words = text.split(" ")
    for i, word in enumerate(words):
        chunk_data = {
            "type": "textDelta",
            "text": f" {word}" if i > 0 else word,
        }
        yield f"data: {json.dumps(chunk_data)}\n\n"
        await asyncio.sleep(0.02)

    # Send final message with token usage
    final_chunk = {
        "type": "messageDelta",
        "delta": {"role": "assistant"},
        "usage": {"output_tokens": tokens.get("output", 0)}
    }
    yield f"data: {json.dumps(final_chunk)}\n\n"

    # Send message stop
    stop_chunk = {
        "type": "messageStop",
    }
    yield f"data: {json.dumps(stop_chunk)}\n\n"

async def stream_ai_response_with_images(message: str, model_id: str, session_id: str = "default", images: List[ImageData] = None, history: List[Dict[str, Any]] = None):
    """Complete streaming with decision tree, XML processing, and node updates"""
    global decision_tree
    
    try:
        add_server_log("system", f"Processing [{session_id}]: {message[:30]}...")
        
        # Ensure session exists
        if session_id not in decision_tree.conversations:
            decision_tree.start_session(session_id, chat_mode=True)
            add_server_log("triage", f"NEW SESSION STARTED: {session_id}", level="info", details={
                "session_id": session_id,
                "initial_node": "start",
                "timestamp": datetime.now().isoformat()
            })
            # Send initial UI reload signal for left sidebar
            yield f"data: {json.dumps({'type': 'session_started', 'session_id': session_id, 'reload_left_ui': True, 'call_status_api': True})}\n\n"
        
        # Get current node info from decision tree
        state = decision_tree.conversations[session_id]
        current_node = decision_tree.nodes[state.current_node_id]
        
        add_server_log("triage", f"PROCESSING MESSAGE: {session_id} at node {current_node.id}", level="info", details={
            "session_id": session_id,
            "current_node": current_node.id,
            "current_topic": current_node.topic,
            "message_preview": message[:50],
            "node_children": current_node.children,
            "should_reason": current_node.should_reason
        })
        
        add_server_log("triage", f"GETTING MCP CONTEXT: {session_id}", level="info", details={
            "session_id": session_id,
            "active_clients": mcp_manager.get_active_clients() if hasattr(mcp_manager, 'get_active_clients') else []
        })
        
        with mcp_manager.get_active_context():
            add_server_log("triage", f"MCP CONTEXT ACQUIRED: {session_id}", level="info")
            
            agent = get_or_create_session_agent(session_id, model_id)
            
            add_server_log("triage", f"AGENT ACQUIRED: {session_id}", level="info", details={
                "session_id": session_id,
                "agent_type": type(agent).__name__,
                "has_tools": hasattr(agent, 'tools'),
                "tools_count": len(agent.tools) if hasattr(agent, 'tools') else 0
            })
            
            # Dynamic next node selection based on decision tree structure
            def get_next_node_options(current_node, user_message):
                """Determine possible next nodes based on current node structure and user input"""
                
                # If it's a terminal node, stay at current node
                if current_node.is_terminal:
                    return current_node.id
                
                # If current node has specific routing logic based on response options
                if current_node.response_options and current_node.children:
                    # Create mapping between response options and children
                    if len(current_node.children) == 1:
                        # Single child - go to that child
                        return current_node.children[0]
                    elif len(current_node.children) == len(current_node.response_options):
                        # Each response option maps to a child
                        for i, option in enumerate(current_node.response_options):
                            if any(keyword.lower() in user_message.lower() for keyword in option.lower().split()):
                                return current_node.children[i]
                        # Default to first child if no match
                        return current_node.children[0]
                    else:
                        # Complex routing - let AI decide based on reasoning
                        children_info = []
                        for child_id in current_node.children:
                            child_node = decision_tree.nodes.get(child_id)
                            if child_node:
                                children_info.append(f"{child_id}: {child_node.topic}")
                        return children_info  # Return list for AI to choose from
                
                # If no children, stay at current node
                if not current_node.children:
                    return current_node.id
                
                # Default to first child
                return current_node.children[0]
            
            next_node_candidate = get_next_node_options(current_node, message)
            
            # Build comprehensive prompt based on decision tree context
            decision_context = f"""
Current Node: {current_node.id} - {current_node.topic}
Question: {current_node.question}
Available Response Options: {current_node.response_options}
Current Node Children: {current_node.children}
Should Reason: {current_node.should_reason}
Reasoning Rules: {current_node.reasoning_rules}
"""
            
            if isinstance(next_node_candidate, list):
                # AI needs to choose from multiple options
                node_options = "\n".join([f"- {opt}" for opt in next_node_candidate])
                unified_prompt = f"""You are an AI Triage Assistant. 

{decision_context}

User said: "{message}"

Based on the user's response and the current decision tree context, provide appropriate guidance and determine the next step.

Available next nodes:
{node_options}

IMPORTANT FORMATTING RULES:
- Use **bold text** for important questions, warnings, or key medical information
- Use clear, conversational language
- Highlight urgent situations with appropriate emphasis
- Respond in User Language except for tag key name. tag value can be foreign language.

Choose the most appropriate next node based on the user's input and respond with guidance followed by EXACTLY this XML format:
<decision_tree_status next_node="CHOSEN_NODE_ID" action="Moving to next assessment step" />

IMPORTANT: You MUST always provide available options for user interaction. Include quick response options in this format:
<available_options>
<option urgency="normal">Continue with assessment</option>
<option urgency="normal">Go back to previous step</option>
<option urgency="normal">Other</option>
</available_options>

Replace CHOSEN_NODE_ID with the most appropriate node from the available options."""
            else:
                # Direct routing to specific node
                next_node_info = decision_tree.nodes.get(next_node_candidate)
                next_node_options = next_node_info.response_options if next_node_info else []
                
                # Always generate available_options XML - either from next node or fallback options
                available_options_xml = ""
                if next_node_options:
                    options_list = []
                    for option in next_node_options:
                        # Determine urgency based on keywords
                        urgency = "high" if any(keyword in option.lower() for keyword in 
                                              ["emergency", "severe", "urgent", "call 911", "immediate"]) else "normal"
                        options_list.append(f'<option urgency="{urgency}">{option}</option>')
                    
                    # Always add "Other" option for free-form chat
                    options_list.append('<option urgency="normal">Other</option>')
                    
                    available_options_xml = f"""

IMPORTANT: You MUST provide quick response options for user interaction:
<available_options>
{chr(10).join(options_list)}
</available_options>"""
                else:
                    # Fallback options when next node has no response_options
                    available_options_xml = f"""

IMPORTANT: You MUST provide quick response options for user interaction:
<available_options>
<option urgency="normal">Continue with assessment</option>
<option urgency="normal">Go back to previous step</option>
<option urgency="normal">Other</option>
</available_options>"""
                
                unified_prompt = f"""You are an AI Triage Assistant.

{decision_context}

User said: "{message}"

Based on the user's response and the current decision tree context, provide appropriate guidance and then proceed to the next step.

IMPORTANT FORMATTING RULES:
- Use **bold text** for important questions, warnings, or key information
- Use clear, conversational language
- Highlight urgent situations with appropriate emphasis

Respond with guidance followed by EXACTLY this XML format:
<decision_tree_status next_node="{next_node_candidate}" action="Moving to next assessment step" />{available_options_xml}"""
            
            accumulated_response = ""
            
            add_server_log("triage", f"STARTING LLM STREAM: {session_id}", level="info", details={
                "session_id": session_id,
                "prompt_length": len(unified_prompt),
                "agent_tools_count": len(agent.tools) if hasattr(agent, 'tools') else 0,
                "next_node_candidate": str(next_node_candidate)
            })
            
            # Simplified Strands streaming - process events as they come
            xml_processed = False
            xml_buffer = ""  # Buffer to handle XML tags split across chunks
            try:
                async for event in agent.stream_async(unified_prompt):
                    if "data" in event:
                        text_data = event["data"]
                        accumulated_response += text_data
                        
                        # Add to XML buffer for processing
                        xml_buffer += text_data
                        
                        # Check for XML in accumulated response for node transitions
                        if not xml_processed:
                            decision_tree_match = re.search(r'<decision_tree_status[^>]*next_node="([^"]+)"[^>]*/?>', accumulated_response)
                            if decision_tree_match:
                                xml_processed = True
                                next_node_id = decision_tree_match.group(1)
                                
                                add_server_log("triage", f"XML DETECTED: {session_id} -> {next_node_id}", level="info")
                                
                                if next_node_id in decision_tree.nodes:
                                    decision_tree.set_current_node(session_id, next_node_id)
                                    yield f"data: {json.dumps({'type': 'node_changed', 'node_id': next_node_id, 'reload_left_ui': True, 'call_status_api': True})}\n\n"
                        
                        # Send all text - let frontend handle filtering
                        if text_data.strip():
                            yield f"data: {json.dumps({'type': 'content', 'content': text_data})}\n\n"
                    
                    elif "current_tool_use" in event and event["current_tool_use"].get("name"):
                        tool_name = event["current_tool_use"]["name"]
                        yield f"data: {json.dumps({'type': 'tool_use', 'tool_name': tool_name})}\n\n"
                    
                    elif event.get("complete", False):
                        add_server_log("triage", f"STREAM COMPLETE: {session_id}", level="info")
                        break

            except Exception as llm_error:
                add_server_log("triage", f"LLM STREAM ERROR: {session_id} - {str(llm_error)}", level="error")
                yield f"data: {json.dumps({'type': 'content', 'content': f'Error: {str(llm_error)}'})}\n\n"
        
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Error in chat stream: {e}")
        yield f"data: {json.dumps({'type': 'content', 'content': f'Error: {str(e)}'})}\n\n"
        yield "data: [DONE]\n\n"

async def stream_plain_response(message: str, model_id: str):
    """A very simple streaming response for basic checks"""
    add_server_log("system", f"Starting plain text streaming for: {message[:50]}...")
    
    try:
        # Create simple Strands agent
        model = BedrockModel(
            model_id=model_id,
            temperature=0.7
        )
        
        # Get tools from MCP manager
        tools = mcp_manager.get_all_tools(active_only=True)
        
        agent = Agent(
            model=model,
            system_prompt="You are a helpful AI assistant. Use available tools when needed to answer user questions.",
            tools=tools
        )
        
        with mcp_manager.get_active_context():
            # Execute agent and get response
            response = agent(message)
            response_text = str(response)
            
            # Stream response in chunks
            chunk_size = 40
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i+chunk_size]
                yield chunk
                await asyncio.sleep(0.08)  # Small delay for streaming effect
                
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        add_server_log("system", f"Plain text streaming error: {str(e)[:50]}...")
        yield error_msg

@app.get("/")
async def root():
    return {
        "message": "AI Triage Agent API", 
        "status": "online",
        "version": "2.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/models")
async def get_models():
    return AVAILABLE_MODELS

@app.get("/mcp/servers")
async def get_mcp_servers():
    """Get all MCP servers with their current status"""
    return mcp_servers

class ToggleRequest(BaseModel):
    enabled: bool

@app.post("/mcp/servers/{server_name}/toggle")
async def toggle_mcp_server(server_name: str, request: ToggleRequest):
    """Toggle MCP server enabled/disabled state"""
    global mcp_servers
    
    if server_name not in mcp_servers:
        raise HTTPException(status_code=404, detail="Server not found")
    
    enabled = request.enabled
    
    # Update server state
    mcp_servers[server_name]["enabled"] = enabled
    mcp_servers[server_name]["status"] = "ready" if enabled else "disabled"
    
    # Save to configuration file
    save_mcp_config(mcp_servers)
    
    # Update MCP client active state and refresh agent cache
    mcp_manager.set_client_active(server_name, enabled)
    refresh_agents()
    
    action = "enabled" if enabled else "disabled"
    add_server_log(server_name, f"Server {action}")
    
    return {"success": True, "server": server_name, "enabled": enabled}

@app.get("/mcp/logs")
async def get_mcp_logs():
    return server_logs

@app.delete("/mcp/logs")
async def clear_mcp_logs():
    global server_logs
    server_logs.clear()
    add_server_log("system", "Logs cleared")
    return {"message": "Logs cleared"}

@app.post("/mcp/initialize")
async def initialize_mcp():
    """Initialize all MCP servers"""
    try:
        initialize_mcp_servers()
        mcp_manager.initialize_default_clients()
        refresh_agents()  # This will refresh tools cache and clear agents
        return {"message": "MCP servers initialized", "status": "success"}
    except Exception as e:
        add_server_log("system", f"Initialization error: {str(e)}")
        return {"message": f"Initialization failed: {str(e)}", "status": "error"}

@app.get("/mcp/tools")
async def get_mcp_tools_endpoint():
    """Get all available MCP tools from cache"""
    try:
        tools = get_cached_tools()
        tool_info = []
        
        for tool in tools:
            # Extract tool information safely
            tool_data = {
                "name": getattr(tool, 'name', 'unknown'),
                "description": getattr(tool, 'description', ''),
                "type": tool.__class__.__name__
            }
            tool_info.append(tool_data)
        
        return {
            "tools": tool_info,
            "count": len(tools),
            "last_updated": tools_last_updated.isoformat() if tools_last_updated else None
        }
    except Exception as e:
        return {"error": str(e), "tools": [], "count": 0}

@app.get("/agents/status")
async def get_agents_status():
    """Get cached session agents status"""
    agents_info = {}
    for agent_key, agent in session_agents.items():
        session_id, model_id = agent_key.split(":", 1)
        agents_info[agent_key] = {
            "session_id": session_id,
            "model_id": model_id,
            "created": True,
            "tools_count": len(agent.tools) if hasattr(agent, 'tools') and agent.tools else 0
        }
    
    return {
        "session_agents": agents_info,
        "count": len(session_agents)
    }

@app.post("/agents/refresh")
async def refresh_agents_endpoint():
    """Refresh all cached agents"""
    refresh_agents()
    return {"message": "Agent cache refreshed", "status": "success"}

@app.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear a specific session's agent and triage session"""
    global session_agents, decision_tree
    
    # Remove all agents for this session
    keys_to_remove = [key for key in session_agents.keys() if key.startswith(f"{session_id}:")]
    for key in keys_to_remove:
        del session_agents[key]
    
    # Remove triage session if exists
    if decision_tree and session_id in decision_tree.conversations:
        del decision_tree.conversations[session_id]
        add_server_log("triage", f"Cleared triage session: {session_id}")
    
    add_server_log("system", f"Cleared session: {session_id}")
    return {"message": f"Session {session_id} cleared", "status": "success"}

@app.get("/sessions")
async def get_sessions():
    """Get all active sessions"""
    sessions = {}
    for agent_key in session_agents.keys():
        session_id, model_id = agent_key.split(":", 1)
        if session_id not in sessions:
            sessions[session_id] = []
        sessions[session_id].append(model_id)
    
    return {"sessions": sessions, "count": len(sessions)}

@app.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str, model_id: str = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"):
    """Get message history for a specific session"""
    
    # Check if the session exists in our in-memory store
    try:
        # Get messages from the actual agent
        messages = get_session_messages_for_ui(session_id, model_id)
        
        agent_key = f"{session_id}:{model_id}"
        exists = agent_key in session_agents
        
        add_server_log("system", f"Session history request: {session_id} - Found {len(messages)} messages, exists: {exists}")
        
        return {
            "messages": messages,
            "session_id": session_id,
            "model_id": model_id,
            "exists": exists,
            "count": len(messages)
        }
        
    except Exception as e:
        add_server_log("system", f"Error getting session history: {str(e)}")
        return {"messages": [], "session_id": session_id, "exists": False, "error": str(e)}

@app.post("/chat")
async def chat_endpoint(chat_message: ChatMessage, request: Request):
    """Chat endpoint using Strands Agent with streaming"""
    try:
        # Check if model is available
        model_ids = [model["id"] for model in AVAILABLE_MODELS]
        if chat_message.model_id not in model_ids:
            raise HTTPException(status_code=400, detail="Model not available")

        # Check if client accepts streaming
        accept_header = request.headers.get("accept", "")
        if "text/event-stream" in accept_header:
            # Return SSE streaming response
            return StreamingResponse(
                stream_ai_response_with_images(
                    chat_message.message, 
                    chat_message.model_id, 
                    chat_message.session_id,
                    chat_message.images,
                    chat_message.history
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "X-Accel-Buffering": "no",
                }
            )
        elif "text/plain" in accept_header:
            # Return plain text streaming
            return StreamingResponse(
                stream_plain_response(chat_message.message, chat_message.model_id),
                media_type="text/plain"
            )
        else:
            # Default SSE streaming
            return StreamingResponse(
                stream_ai_response_with_images(
                    chat_message.message, 
                    chat_message.model_id, 
                    chat_message.session_id,
                    chat_message.images,
                    chat_message.history
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                }
            )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        add_server_log("system", f"Chat error: {str(e)[:50]}...")
        raise HTTPException(status_code=500, detail=str(e))

# Decision Tree Graph and Triage APIs
@app.get("/api/decision-tree")
async def get_decision_tree():
    """Get the decision tree structure for visualization"""
    try:
        tree_file = os.path.join(os.path.dirname(__file__), 'data/comprehensive_decision_tree.json')
        decision_tree = DecisionTree(tree_file)
        
        # Convert decision tree to JSON-serializable format
        tree_data = {}
        for node_id, node in decision_tree.nodes.items():
            tree_data[node_id] = {
                "id": node.id,
                "topic": node.topic,
                "question": node.question,
                "ui_display": node.ui_display,
                "response_options": node.response_options,
                "children": node.children,
                "is_terminal": node.is_terminal,
                "outcome": node.outcome
            }
        
        return {
            "nodes": tree_data,
            "total_nodes": len(tree_data),
            "entry_point": "start"
        }
        
    except Exception as e:
        add_server_log("triage", f"Error getting decision tree: {str(e)}", level="error")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/triage/session/{session_id}")
async def get_triage_session_state(session_id: str):
    """Get the current state of a triage session"""
    try:
        global decision_tree
        add_server_log("triage", f"Session state requested: {session_id}", level="info")
        
        if not decision_tree:
            add_server_log("triage", "Decision tree not initialized for session request", level="warning")
            return {"error": "Decision tree not initialized"}
        
        if session_id not in decision_tree.conversations:
            add_server_log("triage", f"Session not found: {session_id}", level="info")
            return {
                "session_id": session_id,
                "exists": False,
                "message": "Session not found"
            }
        
        session_state = decision_tree.conversations[session_id]
        current_node = decision_tree.nodes.get(session_state.current_node_id)
        
        if not current_node:
            add_server_log("triage", f"Invalid session state for {session_id}: node {session_state.current_node_id} not found", level="error")
            raise HTTPException(status_code=500, detail="Invalid session state")
        
        add_server_log("triage", f"SESSION STATE API: {session_id} at node {current_node.id}", level="info", details={
            "session_id": session_id,
            "current_node": current_node.id,
            "current_topic": current_node.topic,
            "is_terminal": current_node.is_terminal,
            "children_count": len(current_node.children),
            "response_options_count": len(current_node.response_options),
            "created_at": session_state.created_at.isoformat(),
            "last_updated": session_state.last_updated.isoformat()
        })
        
        return {
            "session_id": session_id,
            "exists": True,
            "current_node_id": session_state.current_node_id,
            "current_node": {
                "id": current_node.id,
                "topic": current_node.topic,
                "question": current_node.question,
                "ui_display": current_node.ui_display,
                "response_options": current_node.response_options,
                "is_terminal": current_node.is_terminal,
                "outcome": current_node.outcome
            },
            "conversation_history": session_state.conversation_history,
            "user_responses": session_state.user_responses,
            "reasoning_trail": session_state.reasoning_trail,
            "chat_mode": session_state.chat_mode,
            "completed": session_state.completed,
            "created_at": session_state.created_at.isoformat(),
            "last_updated": session_state.last_updated.isoformat()
        }
        
    except Exception as e:
        add_server_log("triage", f"Error getting triage session: {str(e)}", level="error")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/triage/status")
async def get_triage_system_status():
    """Get the status of the AI Triage Agent system"""
    try:
        global decision_tree
        add_server_log("triage", "Status API called", level="info")
        
        if not decision_tree:
            add_server_log("triage", "Decision tree not initialized", level="warning")
            return {
                "status": "offline", 
                "message": "Decision tree not initialized",
                "nodes_loaded": 0,
                "tree": None
            }
        
        # Convert decision tree to JSON-serializable format for visualization
        tree_data = {}
        for node_id, node in decision_tree.nodes.items():
            tree_data[node_id] = {
                "id": node.id,
                "topic": node.topic,
                "question": node.question,
                "children": node.children,
                "is_terminal": node.is_terminal,
                "outcome": node.outcome
            }
        
        add_server_log("triage", f"Status returned: {len(decision_tree.nodes)} nodes loaded", level="info")
        
        return {
            "status": "online",
            "nodes_loaded": len(decision_tree.nodes) if decision_tree.nodes else 0,
            "tree": {"nodes": tree_data},
            "message": "AI Triage Agent system ready"
        }
        
    except Exception as e:
        add_server_log("triage", f"Triage system error: {str(e)}", level="error")
        return {
            "status": "offline", 
            "message": f"Triage system unavailable: {str(e)}",
            "nodes_loaded": 0,
            "tree": None
        }

@app.on_event("startup")
async def startup_event():
    """Initialize MCP servers and decision tree on startup"""
    global decision_tree
    
    try:
        initialize_mcp_servers()
    except Exception as e:
        logger.error(f"Failed to initialize MCP servers: {e}")
        add_server_log("system", f"Startup MCP init failed: {str(e)}")
    
    # Initialize decision tree
    try:
        tree_file = os.path.join(os.path.dirname(__file__), 'data/comprehensive_decision_tree.json')
        decision_tree = DecisionTree(tree_file)
        add_server_log("system", f"Decision Tree initialized: {len(decision_tree.nodes)} nodes loaded", level="info")
    except Exception as e:
        add_server_log("system", f"Decision Tree initialization failed: {str(e)}", level="error")
        decision_tree = None

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup MCP servers on shutdown"""
    add_server_log("system", "Shutting down MCP servers...")
    # Clean shutdown for stdio-based servers happens automatically

if __name__ == "__main__":
    import uvicorn
    
    # Set AWS region if not set
    if not os.environ.get('AWS_REGION'):
        os.environ['AWS_REGION'] = 'us-east-1'
    
    add_server_log("system", "Backend starting...")
    print("🚀 Starting AI Triage Agent Backend")
    print("📊 Using Strands Agents for AI processing")
    print("🔧 MCP servers will initialize automatically (stdio transport)")
    print(f"🌍 AWS Region: {os.environ.get('AWS_REGION', 'us-east-1')}")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)