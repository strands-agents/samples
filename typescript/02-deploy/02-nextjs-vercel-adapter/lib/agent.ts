/**
 * Agent factory.
 *
 * Assembles the Strands `Agent` that runs the loop server-side:
 * - model:   a Vercel AI SDK provider wrapped by `VercelModel`
 * - tools:   Zod-typed tools executed inside the loop
 * - plugins: the `SessionManager` (persistence) + `LoggingPlugin` (hooks)
 *
 * The agent is created per request so each request can bind its own session id.
 */
import { Agent } from "@strands-agents/sdk";
import { createModel } from "./model";
import { tools } from "./tools";
import { LoggingPlugin } from "./hooks";
import { createSessionManager } from "./session";

const SYSTEM_PROMPT = [
  "You are a helpful, concise assistant built with the Strands Agents SDK.",
  "Use the provided tools when they help answer accurately (math, current time).",
  "Prefer calling a tool over guessing at a calculation or the current time.",
].join(" ");

export async function createAgent(sessionId: string): Promise<Agent> {
  const [model, sessionManager] = await Promise.all([
    createModel(),
    createSessionManager(sessionId),
  ]);

  return new Agent({
    model,
    systemPrompt: SYSTEM_PROMPT,
    tools,
    // A SessionManager is a plugin; LoggingPlugin registers the lifecycle hooks.
    plugins: [sessionManager, new LoggingPlugin()],
  });
}
