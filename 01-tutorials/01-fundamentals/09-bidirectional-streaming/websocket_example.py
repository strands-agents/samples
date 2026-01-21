"""FastAPI WebSocket Example for BidiAgent - Real-time Voice Conversations
"""

import json
import logging
import os
import sys
import threading
import time
from pathlib import Path

import uvicorn
import webbrowser
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from strands.experimental.bidi.agent import BidiAgent
from strands.experimental.bidi.models.gemini_live import BidiGeminiLiveModel
from strands.experimental.bidi.models.nova_sonic import BidiNovaSonicModel
from strands.experimental.bidi.models.openai_realtime import BidiOpenAIRealtimeModel
from strands.experimental.bidi.types.events import (
    BidiAudioInputEvent,
    BidiImageInputEvent,
    BidiTextInputEvent,
)
from strands_tools import calculator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_available_models():
    """Check which models have valid credentials."""
    available = {
        "novasonic": bool(
            (os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"))
            or os.environ.get("AWS_PROFILE")
        ),
        "gemini": bool(os.environ.get("GOOGLE_API_KEY")),
        "openai": bool(os.environ.get("OPENAI_API_KEY")),
    }
    
    for model, is_available in available.items():
        status = "✓" if is_available else "✗"
        logger.info(f"{status} {model.title()} {'available' if is_available else 'unavailable'}")
    
    return available


app = FastAPI(title="BidiAgent WebSocket Example")
SCRIPT_DIR = Path(__file__).parent
HTML_FILE = SCRIPT_DIR / "websocket_client.html"
    
    
@app.get("/")
async def get(request: Request):
    """Serve the HTML client."""
    with open(HTML_FILE, "r") as f:
        html_content = f.read()
    
    ws_base_url = f"ws://{request.url.hostname}:{request.url.port}"
    html_content = html_content.replace("WS_BASE_URL_PLACEHOLDER", ws_base_url)
    
    available_models = check_available_models()
    html_content = html_content.replace("AVAILABLE_MODELS_PLACEHOLDER", json.dumps(available_models))
    
    return HTMLResponse(html_content)
    
    
@app.websocket("/ws/{model_name}")
async def websocket_endpoint(websocket: WebSocket, model_name: str):
    """WebSocket endpoint for BidiAgent communication."""
    await websocket.accept()
    logger.info(f"Connected: {model_name}")

    if model_name == "novasonic":
        model = BidiNovaSonicModel(
            region="us-east-1",
            model_id="amazon.nova-2-sonic-v1:0",
            provider_config={
                "audio": {
                    "input_sample_rate": 16000,
                    "output_sample_rate": 16000,
                    "voice": "matthew",
                }
            },
            tools=[calculator],
        )
    elif model_name == "gemini":
        model = BidiGeminiLiveModel(client_config={"api_key": os.environ.get("GOOGLE_API_KEY")})
    elif model_name == "openai":
        model = BidiOpenAIRealtimeModel()
    else:
        await websocket.close(code=1003, reason=f"Invalid model: {model_name}")
        return

    agent = BidiAgent(
        model=model,
        tools=[calculator],
        system_prompt="You are a helpful assistant with access to a calculator tool.",
    )

    async def receive_and_convert():
        """Convert WebSocket JSON to event objects, stripping 'type' field."""
        data = await websocket.receive_json()

        if not isinstance(data, dict) or "type" not in data:
            return data

        event_type = data["type"]
        event_data = {k: v for k, v in data.items() if k != "type"}

        if event_type == "bidi_audio_input":
            return BidiAudioInputEvent(**event_data)
        elif event_type == "bidi_text_input":
            return BidiTextInputEvent(**event_data)
        elif event_type == "bidi_image_input":
            return BidiImageInputEvent(**event_data)
        else:
            return data

    try:
        await agent.run(inputs=[receive_and_convert], outputs=[websocket.send_json])
    except WebSocketDisconnect:
        logger.info("Disconnected")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        logger.info("Connection closed")
    
    
if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    url = f"http://localhost:{port}"

    def open_browser():
        time.sleep(1.5)
        logger.info(f"Opening browser at {url}")
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()
    logger.info(f"Starting server on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)