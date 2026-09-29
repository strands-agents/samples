"""Agent construction: model provider, telemetry, session store, and tools.

- ``configure_telemetry`` wires OpenTelemetry export once at startup.
- ``build_model`` selects Amazon Bedrock or OpenAI from configuration.
- ``build_agent`` assembles a per-request agent with a SQLite-backed session
  manager and the local + MCP tools.
"""

from __future__ import annotations

import logging
from typing import Any

from strands import Agent
from strands.models import BedrockModel
from strands.telemetry import StrandsTelemetry

from .config import Settings
from .session_store import SQLiteSessionManager
from .tools import LOCAL_TOOLS

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a helpful, concise assistant. You have tools to tell the time, do "
    "arithmetic, look up the weather, and look up company FAQs. Use a tool only "
    "when it genuinely helps answer the user; otherwise answer directly."
)


def configure_telemetry(settings: Settings) -> None:
    """Configure OpenTelemetry export once at application startup.

    Exports to the configured OTLP endpoint when set; otherwise falls back to
    the console exporter so traces are still visible during local runs.
    """
    telemetry = StrandsTelemetry()
    if settings.otel_exporter_otlp_endpoint:
        telemetry.setup_otlp_exporter()
        logger.info("OTel: exporting to OTLP endpoint %s", settings.otel_exporter_otlp_endpoint)
    else:
        telemetry.setup_console_exporter()
        logger.info("OTel: no OTLP endpoint set, using console exporter")
    telemetry.setup_meter()


def build_model(settings: Settings) -> Any:
    """Build the model provider selected by configuration (Bedrock or OpenAI)."""
    if settings.model_provider == "openai":
        # Imported lazily so Bedrock-only installs don't require the openai extra.
        from strands.models.openai import OpenAIModel

        return OpenAIModel(
            client_args={"api_key": settings.openai_api_key},
            model_id=settings.openai_model_id,
        )

    # Bedrock: use an explicit boto3 session when a profile is configured, so
    # named AWS profiles (e.g. SSO/login profiles) work; otherwise fall back to
    # the default credential chain with the configured region.
    if settings.aws_profile:
        import boto3

        session = boto3.Session(profile_name=settings.aws_profile, region_name=settings.aws_region)
        return BedrockModel(boto_session=session, model_id=settings.bedrock_model_id)
    return BedrockModel(region_name=settings.aws_region, model_id=settings.bedrock_model_id)


def build_agent(
    settings: Settings,
    session_id: str,
    mcp_tools: list[Any] | None = None,
) -> tuple[Agent, SQLiteSessionManager]:
    """Build an agent for a session, seeded from the SQLite session store.

    Args:
        settings: Application settings.
        session_id: Session identifier; history is restored/persisted under it.
        mcp_tools: Tools loaded from the MCP server, added alongside local tools.

    Returns:
        A tuple of the constructed agent and its session manager (so the caller
        can close the SQLite connection when done).
    """
    session_manager = SQLiteSessionManager(session_id=session_id, db_path=settings.session_db_path)
    tools = [*LOCAL_TOOLS, *(mcp_tools or [])]
    agent = Agent(
        model=build_model(settings),
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        session_manager=session_manager,
        agent_id="assistant",
        trace_attributes={"service.name": settings.otel_service_name},
    )
    return agent, session_manager
