import json
import os
import logging 
import random
import re

from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import calculator, http_request, current_time, use_aws
from strands.tools.mcp import MCPClient

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
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

# Define tools
#  http_request, current_time, use_aws
tools = [calculator, http_request, use_aws]  # Define your tools here

# Define classes
class CSAgent(Agent):
    def __init__(self, 
                 system_prompt, 
                 model, 
                 user_id):

        # load previous messages if any
        messages = self.restore_agent_state(user_id)
        super().__init__(system_prompt=system_prompt, 
                         model=model,
                         tools=tools,
                         callback_handler=None,
                         messages=messages,
                        load_tools_from_directory=False
                    )
        logger.debug(f"tools available: {self.tool_names}")

    # Restore agent state
    def restore_agent_state(self, user_id):
        # Retrieve state
        try:
            with open(f"sessions/{user_id}.json", "r") as f:
                state = json.load(f)
                return state["messages"]
        except FileNotFoundError:
                return []
    # Save agent state
    def save_agent_state(self, user_id):
        os.makedirs("sessions", exist_ok=True)

        state = {
            "messages": self.messages
        }
        # Store state (e.g., database, file system, cache)
        with open(f"sessions/{user_id}.json", "w") as f:
            json.dump(state, f)

class PromptRequest(BaseModel):
    prompt: str
    userId: str

# Constants
SYSTEM_PROMPT = """You are a helppful assistant powered by Strands 
Strands Agents is a simple-to-use, code-first framework for building agents - open source by AWS. 
The user has the ability to modify your set of built-in tools. Every time your tool set is changed, you can
propose a new set of tasks that you can do.
"""

# Global variables
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    region_name='us-west-2',
    temperature=0.3,
)

# FastAPI app setup
app = FastAPI()

# Add CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helper functions
def load_prompt_from_file(prompt_name):
    """Load a prompt from a file in the prompts directory."""
    prompts_dir = "prompts"
    os.makedirs(prompts_dir, exist_ok=True)
    
    try:
        with open(f"{prompts_dir}/{prompt_name}.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Warning: Prompt file '{prompt_name}.txt' not found. Using default prompt.")
        return None

# API endpoints
@app.get("/get_conversations")
def get_conversations(userId: str):
    try:
        agent = CSAgent(
            model=bedrock_model,
            system_prompt=SYSTEM_PROMPT,
            user_id=userId
        )
        return {"messages": agent.messages}
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting conversations: {str(e)}")

@app.post("/cs_agent")
def get_agent_response(request: PromptRequest):
    try:
        agent = CSAgent(
            model=bedrock_model,
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
        }
    except Exception as e:
        logger.error(f"Error processing agent response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing agent response: {str(e)}")

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

static_dir = "./static"
print(f"Current working directory: {os.getcwd()}")
print(f"Static directory exists: {os.path.exists(static_dir)}")

@app.get("/")
def read_root():
    return FileResponse("./static/index.html")

# Mount the frontend directory to serve static files
app.mount("/", StaticFiles(directory="./static"), name="frontend")