import json
import os
import logging
import re
import boto3
from botocore.exceptions import ClientError
from typing import Optional

from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import (
    agent_graph, calculator, cron, current_time, editor, environment, 
    file_read, file_write, generate_image, http_request, image_reader, journal, 
    load_tool, mem0_memory, memory, nova_reels, python_repl, retrieve, shell, 
    slack, speak, stop, swarm, think, use_aws, use_llm, workflow
)

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


# Configure logging
logger = logging.getLogger("strands")
logger.setLevel(logging.DEBUG)

logger = logging.getLogger("agent-web-service")
logger.setLevel(logging.DEBUG)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", 
    handlers=[logging.StreamHandler()]
)

def validate_user_id(user_id: str) -> bool:
    """Validate user_id to prevent path traversal attacks."""
    if not user_id:
        return False
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', user_id))

# table name for session managament
table_name = os.environ.get('TABLE_NAME') or None
table_region = os.environ.get('TABLE_REGION') or None
primary_key = os.environ.get('PRIMARY_KEY') or None

# dummy in-line python tool to showcase how to define an inline tool + adding it to the playground
@tool
def weather_forecast(city: str, days: int = 3) -> str:
    """Get weather forecast for a city.

    Args:
        city: The name of the city
        days: Number of days for the forecast
    """
    return f"Weather forecast for {city} for the next {days} days..."

# Define all available tools
available_tools = {
    'agent_graph': agent_graph,
    'calculator': calculator,
    'cron': cron,
    'current_time': current_time,
    'editor': editor,
    'environment': environment,
    'file_read': file_read,
    'file_write': file_write,
    'generate_image': generate_image,
    'http_request': http_request,
    'image_reader': image_reader,
    'journal': journal,
    'load_tool': load_tool,
    'mem0_memory': mem0_memory,
    'memory': memory,
    'nova_reels': nova_reels,
    'python_repl': python_repl,
    'retrieve': retrieve,
    'shell': shell,
    'slack': slack,
    'speak': speak,
    'stop': stop,
    'swarm': swarm,
    'think': think,
    'use_aws': use_aws,
    'use_llm': use_llm,
    'workflow': workflow,
    'weather_forecast': weather_forecast,
}

# Tool descriptions for better user understanding
tool_descriptions = {
    'agent_graph': 'Create and manage graphs of agents with different topologies and communication patterns',
    'calculator': 'Perform mathematical calculations with support for advanced operations',
    'cron': 'Manage crontab entries for scheduling tasks, with special support for Strands agent jobs',
    'current_time': 'Get the current time in various timezones',
    'editor': 'Editor tool designed to do changes iteratively on multiple files',
    'environment': 'Manage environment variables at runtime',
    'file_read': 'File reading tool with search capabilities, various reading modes, and document mode support',
    'file_write': 'Write content to a file with proper formatting and validation based on file type',
    'generate_image': 'Create images using Stable Diffusion models',
    'http_request': 'Make HTTP requests to external APIs with authentication support',
    'image_reader': 'Read and process image files for AI analysis',
    'journal': 'Create and manage daily journal entries with tasks and notes',
    'load_tool': 'Dynamically load Python tools at runtime',
    'mem0_memory': 'Memory management tool for storing, retrieving, and managing memories in Mem0',
    'memory': 'Store and retrieve data in Bedrock Knowledge Base',
    'nova_reels': 'Create high-quality videos using Amazon Nova Reel',
    'python_repl': 'Execute Python code in a REPL environment with PTY support and state persistence',
    'retrieve': 'Retrieves knowledge based on the provided text from Amazon Bedrock Knowledge Bases',
    'shell': 'Interactive shell with PTY support for real-time command execution and interaction',
    'slack': 'Comprehensive Slack integration for messaging, events, and interactions',
    'speak': 'Generate speech from text using say command or Amazon Polly.',
    'stop': 'Stops the current event loop cycle by setting stop_event_loop flag',
    'swarm': 'Create and coordinate a swarm of AI agents for parallel processing and collective intelligence',
    'think': 'Process thoughts through multiple recursive cycles',
    'use_aws': 'Execute AWS service operations using boto3',
    'use_llm': 'Create isolated agent instances for specific tasks',
    'workflow': 'Advanced workflow orchestration system for parallel AI task execution',
    'weather_forecast': 'Return a dummy weather for the input city and day, used to showcase inline python tool for Strands'
}

# Define default selected tools
tools = [calculator, http_request, use_aws]  # Default tools

# Define classes
class StrandsPlaygroundAgent(Agent):
    def __init__(self, 
                 system_prompt, 
                 model, 
                 user_id):

        # load previous messages if any
        messages = self.restore_agent_state(user_id)
        super().__init__(system_prompt=system_prompt, 
                         model=model,
                         tools=tools,  # Use the global tools list
                         callback_handler=None,
                         messages=messages,
                         load_tools_from_directory=False
                    )
        logger.debug(f"tools available: {self.tool_names}")
    # Restore agent state
    def restore_agent_state(self, user_id):
        if not validate_user_id(user_id):
            logger.error(f"Invalid user_id format")
            raise ValueError("Invalid user_id: must contain only alphanumeric characters, underscores, or hyphens")
        if not table_name and not table_region:
            logger.debug("TABLE_NAME environment variable not set, fallback to local file session.. loading conversation history from file")
            # Retrieve state
            try:
                with open(f"sessions/{user_id}.json", "r") as f:
                    state = json.load(f)
                    return state["messages"]
            except FileNotFoundError:
                    logger.error("Local session file for user not found, returning empty conversation history")
                    return []
        else: 
            try: 
                logger.debug(f"Loading session from dynamodb table: {str(table_name)} in {str(table_region)} region")
                dynamodb = boto3.resource('dynamodb', region_name=table_region)
                table = dynamodb.Table(table_name)
                response = table.get_item(
                Key={
                        primary_key: user_id,
                    }
                )
                if "Item" in response:
                    messages = response['Item']['messages'] 
                    logger.debug("messages returned from Dynamo")
                    logger.debug(messages)
                else: 
                    logger.debug("No messages found in DynamoDB")
                    messages = []
                return messages
            except Exception as e:
                logger.error(f"Failed to restore session from DynamoDB: {str(e)} returning empty conversation history")
                return []

    # Save agent state
    def save_agent_state(self, user_id):
        if not validate_user_id(user_id):
            logger.error(f"Invalid user_id format")
            raise ValueError("Invalid user_id: must contain only alphanumeric characters, underscores, or hyphens")
        if not table_name and not table_region:
            try:
                logger.debug("TABLE_NAME and TABLE_REGION environment variable not set, fallback to local file session management, saving conversation to file")
                os.makedirs("sessions", exist_ok=True)
                state = {
                    "messages": self.messages
                }
                # Store state (e.g., database, file system, cache)
                with open(f"sessions/{user_id}.json", "w") as f:
                    json.dump(state, f)
            except Exception as e:
                logger.error(f"Failed to save session to local file: {str(e)}")
        else:
            try:
                logger.debug(f"Saving conversation to dynamodb table {table_name} in {table_region} region")
                dynamodb = boto3.resource('dynamodb', region_name=table_region)
                table = dynamodb.Table(table_name)
                state = {
                    "messages": self.messages
                }
                table.put_item(
                    Item={
                        primary_key: user_id,
                        'messages': state['messages']
                    }
                )
            except ClientError as e:
                logger.error(f"Failed to save session to dynamodb table {table_name} in {table_region} region")

class PromptRequest(BaseModel):
    prompt: str
    userId: str

class SystemPromptRequest(BaseModel):
    systemPrompt: str
    
class ModelSettingsRequest(BaseModel):
    modelId: str
    region: str
    maxTokens: Optional[int] = None
    temperature: Optional[float] = None
    topP: Optional[float] = None
    
class ToolsUpdateRequest(BaseModel):
    tools: list[str]

# Constants
SYSTEM_PROMPT = """You are a helpful assistant powered by Strands. Strands Agents is a simple-to-use, code-first framework for building agents - open source by AWS. 
The user has the ability to modify your set of built-in tools. Every time your tool set is changed, you can propose a new set of tasks that you can do.
"""

# Global variables
MODEL_ID = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
REGION = "us-west-2"
MAX_TOKENS = 1000
TEMPERATURE = 0.3
TOP_P = 0.9

BEDROCK_MODEL = BedrockModel(
    model_id=MODEL_ID,
    region_name=REGION,
    temperature=TEMPERATURE,
    max_tokens=MAX_TOKENS,
    top_p=TOP_P,
)

# FastAPI app setup
app = FastAPI()


# API endpoints
@app.get("/get_conversations")
def get_conversations(userId: str):
    try:
        agent = StrandsPlaygroundAgent(
            model=BEDROCK_MODEL,
            system_prompt=SYSTEM_PROMPT,
            user_id=userId
        )
        return {"messages": agent.messages}
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting conversations: {str(e)}")

@app.post("/strandsplayground_agent")
def get_agent_response(request: PromptRequest):
    try:
        agent = StrandsPlaygroundAgent(
            model=BEDROCK_MODEL,
            system_prompt=SYSTEM_PROMPT,
            user_id=request.userId
        )
        result = agent(request.prompt)
        logger.debug(f"Model response: {result.message}")
        agent.save_agent_state(request.userId)
        logger.info(f"Agent state saved for user: {request.userId}")
        return {
            "messages": result.message, 
            "latencyMs": result.metrics.accumulated_metrics["latencyMs"],
            "totalTokens": result.metrics.accumulated_usage["totalTokens"],
            "summary": result.metrics.get_summary()
        }
    except Exception as e:
        logger.error(f"Error processing agent response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing agent response: {str(e)}")

# System prompt endpoints
@app.get("/system_prompt")
def get_system_prompt():
    return {"systemPrompt": SYSTEM_PROMPT}

@app.post("/system_prompt")
def set_system_prompt(request: SystemPromptRequest):
    global SYSTEM_PROMPT
    SYSTEM_PROMPT = request.systemPrompt
    return {"systemPrompt": SYSTEM_PROMPT}

# Model settings endpoints
@app.get("/model_settings")
def get_model_settings():
    global BEDROCK_MODEL
    config = BEDROCK_MODEL.get_config()
    return {
        "modelId": MODEL_ID,
        "region": REGION,
        "maxTokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "topP": TOP_P
    }

@app.post("/model_settings")
def set_model_settings(request: ModelSettingsRequest):
    global BEDROCK_MODEL, MODEL_ID, REGION, MAX_TOKENS, TEMPERATURE, TOP_P
    logger.debug(f"received the following when updated the model: {request}")    
   
    # Create a parameters dictionary with only non-None values
    model_params = {
        "model_id": request.modelId,
    }
    
    # Only add parameters if they have values
    if request.maxTokens is not None:
        model_params["max_tokens"] = request.maxTokens
    else: 
        model_params.pop('max_tokens', None)

    if request.temperature is not None:
        model_params["temperature"] = request.temperature
    else:
        model_params.pop('temperature', None)

    if request.topP is not None:
        model_params["top_p"] = request.topP
    else:
        model_params.pop('top_p', None)
    
    
    logger.debug(f"model settings parmaeters passed: {model_params}")

    # Update the bedrock model with new settings
    BEDROCK_MODEL = BedrockModel(**model_params, region_name=request.region)
    REGION = request.region
    MAX_TOKENS = request.maxTokens
    TEMPERATURE = request.temperature
    TOP_P = request.topP
    MODEL_ID = request.modelId

    return {
        "modelId": request.modelId,
        "region": request.region,
        "maxTokens": request.maxTokens,
        "temperature": request.temperature,
        "topP": request.topP
    }

# Tools management endpoints
@app.get("/get_available_tools")
def get_available_tools():
    global tools, available_tools, tool_descriptions
    return {
        "available_tools": list(available_tools.keys()),
        "selected_tools": [tool.__name__.split('.')[-1] for tool in tools],
        "tool_descriptions": tool_descriptions
    }

@app.post("/update_tools")
def update_tools(request: ToolsUpdateRequest):
    global tools, available_tools
    
    try:
        # Validate that all requested tools exist
        for tool_name in request.tools:
            if tool_name not in available_tools:
                raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")
        
        # Update the tools list
        tools = [available_tools[tool_name] for tool_name in request.tools]
        
        logger.info(f"Updated tools list: {[tool.__name__ for tool in tools]}")
        return {"success": True, "selected_tools": [tool.__name__ for tool in tools]}
    except Exception as e:
        logger.error(f"Error updating tools: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating tools: {str(e)}")

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

static_dir = "./static"

@app.get("/")
def read_root():
    return FileResponse("./static/index.html")

# Mount the frontend directory to serve static files
app.mount("/", StaticFiles(directory="./static"), name="frontend")