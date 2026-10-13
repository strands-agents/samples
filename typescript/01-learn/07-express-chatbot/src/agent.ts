/**
 * Agent factory.
 *
 * Builds a per-turn Strands `Agent` wired with:
 *   - a Bedrock model (configurable via env),
 *   - the three local Zod tools plus any MCP tools loaded at startup,
 *   - the rate-limit and moderation interventions,
 *   - the session's prior message history (so the chatbot is stateful),
 *   - `sessionId` in agent state so interventions can meter per session.
 *
 * A fresh agent is created per request and seeded with the stored history.
 * After the turn, the server persists `agent.messages` back into the session.
 */

import { Agent, BedrockModel } from "@strands-agents/sdk";
import { config } from "./config.js";
import { localTools } from "./tools/chatTools.js";
import type { McpTools } from "./mcp/mcpTools.js";
import type { Session } from "./sessions/SessionStore.js";
import type { SessionStore } from "./sessions/SessionStore.js";
import { RateLimitIntervention } from "./interventions/RateLimitIntervention.js";
import { ModerationIntervention } from "./interventions/ModerationIntervention.js";

const SYSTEM_PROMPT = `You are a helpful, concise assistant.

You have tools to:
- get the current time for a timezone,
- perform basic arithmetic,
- look up the current weather for a coordinate.

Use a tool only when it genuinely helps answer the user. Prefer answering
directly for simple questions. If a tool call is blocked by a policy, explain
the limitation briefly and help the user as best you can without it.`;

export interface BuildAgentArgs {
  session: Session;
  sessions: SessionStore;
  mcpTools: McpTools;
}

/** Create an agent for a single chat turn, seeded with session history. */
export function buildAgent({ session, sessions, mcpTools }: BuildAgentArgs): Agent {
  const rateLimit = new RateLimitIntervention(
    sessions,
    config.rateLimit.maxToolCalls,
    config.rateLimit.windowMs,
  );
  const moderation = new ModerationIntervention(config.moderation.blockedTerms);

  return new Agent({
    model: new BedrockModel({
      region: config.model.region,
      modelId: config.model.modelId,
    }),
    systemPrompt: SYSTEM_PROMPT,
    tools: [...localTools, ...mcpTools],
    interventions: [moderation, rateLimit],
    messages: session.messages,
    appState: { sessionId: session.id },
    printer: false,
  });
}
