"""Configuration for the FastAPI + Strands production starter.

Settings are read from environment variables (and an optional ``.env`` file)
via pydantic-settings. Copy ``.env.example`` to ``.env`` to override defaults.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict
from strands.types.agent import Limits


class Settings(BaseSettings):
    """Typed application settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Model provider
    model_provider: Literal["bedrock", "openai"] = "bedrock"
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "us.amazon.nova-pro-v1:0"
    openai_api_key: str | None = None
    openai_model_id: str = "gpt-4o-mini"

    # Lifecycle controls (per-request budget caps)
    max_turns: int = 6
    max_output_tokens: int = 2048
    max_total_tokens: int | None = None

    # Session store
    session_db_path: str = "sessions.db"

    # MCP server
    mcp_server_url: str | None = "http://localhost:8001/mcp"

    # OpenTelemetry
    otel_exporter_otlp_endpoint: str | None = None
    otel_service_name: str = "fastapi-strands-starter"

    def limits(self) -> Limits:
        """Build the per-invocation :class:`Limits` from the configured caps.

        Only positive caps are included; omitted dimensions are unbounded.
        """
        limits: Limits = {}
        if self.max_turns and self.max_turns > 0:
            limits["turns"] = self.max_turns
        if self.max_output_tokens and self.max_output_tokens > 0:
            limits["output_tokens"] = self.max_output_tokens
        if self.max_total_tokens and self.max_total_tokens > 0:
            limits["total_tokens"] = self.max_total_tokens
        return limits


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
