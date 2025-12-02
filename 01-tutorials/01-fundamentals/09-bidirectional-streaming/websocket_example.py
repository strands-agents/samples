"""FastAPI WebSocket Example for BidiAgent - Real-time Voice Conversations
    
This example demonstrates how to integrate BidiAgent with a web application using
WebSocket for real-time bidirectional audio streaming. Perfect for building voice
assistants, conversational AI interfaces, or any application requiring speech-to-speech
interaction.
    
Features Demonstrated:
- Real-time audio streaming (microphone → agent → speakers)
- Live transcription of both user and assistant speech
- Interruption handling (speak over the assistant)
- Tool execution (calculator integration)
- Simple browser-based UI with no additional dependencies
    
Architecture:
    Browser (HTML/JS) ←→ WebSocket ←→ BidiAgent ←→ AI Model (Nova Sonic/Gemini/OpenAI)
    
    - Browser captures microphone audio, encodes to base64 PCM
    - WebSocket forwards audio events bidirectionally
    - BidiAgent processes audio and executes tools
    - Responses stream back as audio + transcripts
    
Setup:
    1. Install dependencies:
        pip install fastapi uvicorn websockets "git+https://github.com/mehtarac/sdk-python.git#egg=strands-agents[bidi-all]" strands-agents-tools
    
    2. Set credentials for your chosen model:
        
        For AWS Nova Sonic:
            export AWS_ACCESS_KEY_ID="your-key"
            export AWS_SECRET_ACCESS_KEY="your-secret"
            export AWS_SESSION_TOKEN="your-token"  # if using temporary credentials
        
        For Google Gemini Live:
            export GOOGLE_API_KEY="your-key"
        
        For OpenAI Realtime:
            export OPENAI_API_KEY="your-key"
    
    3. Run the server:
        python websocket_example.py [port]
        # Default port is 8000, or specify a custom port:
        # python websocket_example.py 8080
        # or: uvicorn websocket_example:app --reload --port 8000
    
    4. Open browser:
        http://localhost:8000 (or your specified port)
    
Usage:
    1. Select your preferred model (AWS Nova Sonic, Google Gemini Live, or OpenAI Realtime)
    2. Click "Start Session" to establish WebSocket connection and start recording
    3. Speak naturally - try "What is 25 times 8?"
    4. The agent will respond with voice and show transcripts
    5. You can interrupt the agent by speaking while it's talking
    6. Click "End Session" to stop
    
Event Flow:
    Client → Server:
        - bidi_connection_start: Initial connection with connection_id and model
          Format: {"type": "bidi_connection_start", "connection_id": "uuid", "model": "model-id"}
        
        - bidi_audio_input: PCM audio chunks from microphone
          Format: {"type": "bidi_audio_input", "audio": "base64", "format": "pcm", "sample_rate": 16000, "channels": 1}
          * Nova Sonic: 16kHz mono
          * Gemini Live: 24kHz mono
          * OpenAI Realtime: 24kHz mono
    
    Server → Client:
        - bidi_audio_stream: PCM audio response from agent
          Format: {"type": "bidi_audio_stream", "audio": "base64", "format": "pcm", "sample_rate": 16000, "channels": 1}
          * Nova Sonic: 16kHz mono
          * Gemini Live: 24kHz mono
          * OpenAI Realtime: 24kHz mono
        
        - bidi_transcript_stream: Real-time transcription with delta updates
          Format: {"type": "bidi_transcript_stream", "delta": {"text": "..."}, "text": "...", "role": "user|assistant", "is_final": true|false, "current_transcript": "..."}
        
        - bidi_usage: Token usage statistics
          Format: {"type": "bidi_usage", "inputTokens": 22, "outputTokens": 0, "totalTokens": 22}
        
        - bidi_interruption: Notification when user interrupts
        - tool_use_stream: Tool execution started
        - tool_result: Tool execution completed
    
For production use, consider:
    - Adding authentication/authorization
    - Implementing rate limiting
    - Using HTTPS/WSS for secure connections
    - Adding error recovery and reconnection logic
    - Monitoring WebSocket connection health
"""
    
import logging
import os
from pathlib import Path
    
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
    
from strands.experimental.bidi.agent.agent import BidiAgent
from strands.experimental.bidi.models.novasonic import BidiNovaSonicModel
from strands.experimental.bidi.models.gemini_live import BidiGeminiLiveModel
from strands.experimental.bidi.models.openai import BidiOpenAIRealtimeModel
from strands_tools import calculator
    
# Configure logging to see connection events and errors
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_available_models():
    """Check which models have valid credentials configured."""
    available = {}
    
    # Check AWS credentials for Nova Sonic
    aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    available["novasonic"] = bool(aws_access_key and aws_secret_key)
    if available["novasonic"]:
        logger.info("✓ AWS credentials found - Nova Sonic available")
    else:
        logger.warning("✗ AWS credentials not found - Nova Sonic unavailable")
    
    # Check Google API key for Gemini
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    available["gemini"] = bool(google_api_key)
    if available["gemini"]:
        logger.info("✓ Google API key found - Gemini Live available")
    else:
        logger.warning("✗ Google API key not found - Gemini Live unavailable")
    
    # Check OpenAI API key
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    available["openai"] = bool(openai_api_key)
    if available["openai"]:
        logger.info("✓ OpenAI API key found - OpenAI Realtime available")
    else:
        logger.warning("✗ OpenAI API key not found - OpenAI Realtime unavailable")
    
    return available
    
# Initialize FastAPI application
app = FastAPI(title="BidiAgent WebSocket Example")

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent
HTML_FILE = SCRIPT_DIR / "websocket_client.html"
    
    
@app.get("/")
async def get(request: Request):
    """Serve the HTML test client.
    
    Returns a simple web interface for testing the BidiAgent WebSocket connection.
    Includes microphone recording, audio playback, and message display.
    """
    # Read the HTML file and inject the WebSocket URL base
    with open(HTML_FILE, "r") as f:
        html_content = f.read()
    
    # Replace the WebSocket URL placeholder with the actual host and port (without /ws path)
    ws_base_url = f"ws://{request.url.hostname}:{request.url.port}"
    html_content = html_content.replace("WS_BASE_URL_PLACEHOLDER", ws_base_url)
    
    # Inject available models
    available_models = check_available_models()
    import json
    available_models_json = json.dumps(available_models)
    html_content = html_content.replace("AVAILABLE_MODELS_PLACEHOLDER", available_models_json)
    
    return HTMLResponse(html_content)
    
    
@app.websocket("/ws/{model_name}")
async def websocket_endpoint(websocket: WebSocket, model_name: str):
    """WebSocket endpoint for real-time bidirectional communication with BidiAgent.
    
    This endpoint demonstrates the simplest possible integration:
    1. Accept WebSocket connection
    2. Create BidiAgent with model and tools
    3. Pass WebSocket send/receive methods directly to agent.run()
    
    The agent handles all the complexity:
    - Audio streaming in both directions
    - Transcript generation
    - Interruption detection
    - Tool execution
    - Event routing
    
    Args:
        websocket: FastAPI WebSocket connection from the client
        model_name: Name of the model to use (novasonic, gemini, openai)
        
    Event Types Handled:
        Incoming (from client):
            - bidi_connection_start: Initial connection setup
            - bidi_audio_input: Audio chunks from microphone (base64 PCM)
            
        Outgoing (to client):
            - bidi_audio_stream: Audio response from agent (base64 PCM)
            - bidi_transcript_stream: Speech transcription with delta, text, role, is_final
            - bidi_usage: Token usage statistics (inputTokens, outputTokens, totalTokens)
            - bidi_interruption: User interrupted agent
            - tool_use_stream: Tool execution started
            - tool_result: Tool execution result
    """
    # Accept the WebSocket connection
    await websocket.accept()
    logger.info(f"WebSocket connection accepted with model: {model_name}")

    # Initialize the model based on selection
    if model_name == "novasonic":
        model = BidiNovaSonicModel(region="us-east-1")
        logger.info("Using Nova Sonic model (Input: 16kHz, Output: 16kHz)")
    elif model_name == "gemini":
        model = BidiGeminiLiveModel(region="us-east-1")
        logger.info("Using Gemini Live model (Input: 24kHz, Output: 24kHz)")
    elif model_name == "openai":
        model = BidiOpenAIRealtimeModel(region="us-east-1")
        logger.info("Using OpenAI Realtime model (Input: 24kHz, Output: 24kHz)")
    else:
        await websocket.close(code=1003, reason=f"Invalid model: {model_name}")
        return

    # Create the BidiAgent with model, tools, and system prompt
    agent = BidiAgent(
        model=model,
        tools=[calculator],  # Add any Strands tools here
        system_prompt="You are a helpful assistant with access to a calculator tool.",
    )

    try:
        # Run the agent with WebSocket transport
        # agent.run() expects a list containing a tuple of (sender, receiver) callables
        # - websocket.send_json: Sends events from agent to client
        # - websocket.receive_json: Receives events from client to agent
        await agent.run(inputs=[websocket.receive_json], outputs=[websocket.send_json])
    except WebSocketDisconnect:
        # Client disconnected normally
        logger.info("WebSocket disconnected")
    except Exception as e:
        # Handle any errors during the session
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        # Cleanup happens automatically via agent context manager
        logger.info("Connection closed")
    
    
if __name__ == "__main__":
    import sys
    import uvicorn
    import webbrowser
    import threading
    import time
    
    # Get port from command line argument or use default
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    url = f"http://localhost:{port}"
    
    # Function to open browser after a short delay
    def open_browser():
        time.sleep(1.5)  # Wait for server to start
        logger.info(f"Opening browser at {url}")
        webbrowser.open(url)
    
    # Start browser opener in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    logger.info(f"Starting server on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)