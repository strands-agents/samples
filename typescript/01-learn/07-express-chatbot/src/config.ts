/**
 * Centralized configuration for the Express + Strands chatbot starter.
 *
 * Reads settings from environment variables with sensible defaults so the
 * sample runs out of the box. Copy `.env.example` to `.env` to override.
 */

/** Parse an integer env var, falling back to a default when unset or invalid. */
function envInt(name: string, fallback: number): number {
  const raw = process.env[name];
  if (!raw) return fallback;
  const parsed = Number.parseInt(raw, 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

/** Parse a comma-separated env var into a trimmed, non-empty string array. */
function envList(name: string): string[] {
  const raw = process.env[name];
  if (!raw) return [];
  return raw
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

export const config = {
  /** HTTP port for the Express server. */
  port: envInt("PORT", 3000),

  model: {
    /** AWS region for the Bedrock model. */
    region: process.env.AWS_REGION ?? "us-east-1",
    /** Bedrock model id used by the chatbot agent. */
    modelId:
      process.env.BEDROCK_MODEL_ID ??
      "us.amazon.nova-pro-v1:0",
  },

  mcp: {
    /**
     * Streamable HTTP URL of an MCP server. Defaults to the public, no-auth
     * AWS Knowledge MCP Server. Set to '' (empty) to disable MCP.
     */
    serverUrl:
      process.env.MCP_SERVER_URL === undefined
        ? "https://knowledge-mcp.global.api.aws"
        : process.env.MCP_SERVER_URL || undefined,
  },

  rateLimit: {
    /** Max tool calls per session within the window. */
    maxToolCalls: envInt("RATE_LIMIT_MAX_TOOL_CALLS", 10),
    /** Rate limit window in milliseconds. */
    windowMs: envInt("RATE_LIMIT_WINDOW_MS", 60_000),
  },

  moderation: {
    /** Blocked terms (case-insensitive). Empty disables moderation. */
    blockedTerms: envList("MODERATION_BLOCKED_TERMS"),
  },
} as const;

export type AppConfig = typeof config;
