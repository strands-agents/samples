"""FastAPI service exposing the Strands agent.

Endpoints
---------
- ``GET  /health`` — liveness and basic runtime info.
- ``POST /chat``   — run one agent turn for a session.

The service wires four production concerns:

1. **Lifecycle controls** — every request passes ``limits`` (max turns and a
   token budget) to ``invoke_async``; when a cap is reached the loop stops
   gracefully with a ``limit_*`` stop reason instead of running unbounded.
2. **Cancellation on client disconnect** — a background watcher polls
   ``request.is_disconnected()`` and sets a ``threading.Event`` passed as
   ``cancel_signal`` so the agent stops promptly when the caller goes away.
3. **Session store** — conversation history is persisted per ``session_id`` in
   SQLite, so turns are stateful across requests and restarts.
4. **MCP + OTel** — an MCP client is connected for the app's lifetime and its
   tools are loaded once; OpenTelemetry export is configured at startup.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from strands.tools.mcp import MCPClient

from .agent_factory import build_agent, configure_telemetry
from .config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Poll interval for the disconnect watcher.
_DISCONNECT_POLL_SECONDS = 0.25


class ChatRequest(BaseModel):
    """Request body for POST /chat."""

    message: str = Field(..., min_length=1, description="The user's message.")
    session_id: str = Field("default", description="Session id; scopes conversation history.")


class ChatResponse(BaseModel):
    """Response body for POST /chat."""

    session_id: str
    reply: str
    stop_reason: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Configure telemetry and connect the MCP client for the app's lifetime."""
    settings = get_settings()
    configure_telemetry(settings)

    mcp_client: MCPClient | None = None
    mcp_tools: list[Any] = []
    if settings.mcp_server_url:
        mcp_client = MCPClient(url=settings.mcp_server_url)
        try:
            mcp_client.start()
            mcp_tools = list(mcp_client.list_tools_sync())
            logger.info(
                "MCP: connected to %s, loaded %d tool(s): %s",
                settings.mcp_server_url,
                len(mcp_tools),
                ", ".join(t.tool_name for t in mcp_tools),
            )
        except Exception as exc:  # noqa: BLE001 - keep the service up if MCP is down
            logger.warning("MCP: could not connect to %s (%s); continuing without MCP tools",
                           settings.mcp_server_url, exc)
            mcp_client = None

    app.state.settings = settings
    app.state.mcp_tools = mcp_tools
    try:
        yield
    finally:
        if mcp_client is not None:
            mcp_client.stop(None, None, None)


app = FastAPI(title="FastAPI + Strands production starter", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, Any]:
    """Liveness check with basic runtime info."""
    settings = app.state.settings
    return {
        "status": "ok",
        "model_provider": settings.model_provider,
        "mcp_tools": [t.tool_name for t in app.state.mcp_tools],
        "limits": settings.limits(),
    }


async def _watch_disconnect(request: Request, cancel_signal: threading.Event) -> None:
    """Set ``cancel_signal`` as soon as the client disconnects."""
    try:
        while not cancel_signal.is_set():
            if await request.is_disconnected():
                logger.info("client disconnected — cancelling agent invocation")
                cancel_signal.set()
                return
            await asyncio.sleep(_DISCONNECT_POLL_SECONDS)
    except asyncio.CancelledError:
        pass


@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    """Run one agent turn with lifecycle limits and cancel-on-disconnect."""
    settings = app.state.settings
    agent, session_manager = build_agent(
        settings, session_id=body.session_id, mcp_tools=app.state.mcp_tools
    )

    # Cancellation driven from outside the agent: a client disconnect.
    cancel_signal = threading.Event()
    watcher = asyncio.create_task(_watch_disconnect(request, cancel_signal))

    try:
        result = await agent.invoke_async(
            body.message,
            limits=settings.limits(),
            cancel_signal=cancel_signal,
        )
    finally:
        watcher.cancel()
        session_manager.close()

    return ChatResponse(
        session_id=body.session_id,
        reply=str(result),
        stop_reason=str(result.stop_reason),
    )
