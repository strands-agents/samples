"""Serves the web client and a single chat endpoint."""

import logging
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent import Chat

logger = logging.getLogger(__name__)
app = FastAPI()
chats: dict[str, Chat] = {}


class ChatRequest(BaseModel):
    chat: str
    message: str


@app.post("/api/chat", response_model=None)
def chat(request: ChatRequest) -> dict | JSONResponse:
    session = chats.setdefault(request.chat, Chat())
    try:
        return session.send(request.message)
    except Exception:
        # A failed turn can leave the conversation history incomplete, so start this chat over.
        chats.pop(request.chat, None)
        logger.exception("chat turn failed")
        return JSONResponse(
            {"error": "The agent hit an error, so this conversation was reset. Please try again."}, status_code=500
        )


app.mount("/", StaticFiles(directory=Path(__file__).parent / "web", html=True))

if __name__ == "__main__":
    # Local demo with no authentication, so it only listens on loopback.
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8000")))
