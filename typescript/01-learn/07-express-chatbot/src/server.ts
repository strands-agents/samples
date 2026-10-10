/**
 * Express application: HTTP surface for the chatbot.
 *
 * Routes:
 *   GET  /health            — liveness + live session count
 *   POST /chat              — non-streaming turn, returns the final reply as JSON
 *   POST /chat/stream       — streaming turn over Server-Sent Events (SSE)
 *
 * Both chat routes accept `{ message: string, sessionId?: string }`. When
 * `sessionId` is omitted a new session is created and its id is returned to
 * the caller (JSON field / SSE `session` event) so subsequent turns can
 * continue the same conversation.
 *
 * The SSE stream forwards each Strands `AgentStreamEvent` as its own SSE
 * message with a monotonically increasing `id:` line, so clients can track
 * position and use `Last-Event-ID` for reconnection semantics.
 */

import express, { type Request, type Response } from "express";
import type { Agent } from "@strands-agents/sdk";
import { buildAgent } from "./agent.js";
import { SessionStore } from "./sessions/SessionStore.js";
import type { McpTools } from "./mcp/mcpTools.js";

export interface CreateServerArgs {
  mcpTools: McpTools;
  sessions?: SessionStore;
}

interface ChatBody {
  message?: unknown;
  sessionId?: unknown;
}

/** Validate and normalize the chat request body. */
function parseChatBody(body: ChatBody): { message: string; sessionId?: string } | null {
  if (typeof body.message !== "string" || body.message.trim().length === 0) {
    return null;
  }
  const sessionId =
    typeof body.sessionId === "string" && body.sessionId.length > 0
      ? body.sessionId
      : undefined;
  return { message: body.message, sessionId };
}

export function createServer({ mcpTools, sessions = new SessionStore() }: CreateServerArgs) {
  const app = express();
  app.use(express.json());

  app.get("/health", (_req: Request, res: Response) => {
    res.json({ status: "ok", sessions: sessions.size });
  });

  // Non-streaming: run the turn to completion and return the final text.
  app.post("/chat", async (req: Request, res: Response) => {
    const parsed = parseChatBody(req.body as ChatBody);
    if (!parsed) {
      res.status(400).json({ error: "Body must include a non-empty 'message' string." });
      return;
    }

    const session = sessions.getOrCreate(parsed.sessionId);
    const agent: Agent = buildAgent({ session, sessions, mcpTools });

    try {
      const result = await agent.invoke(parsed.message);
      sessions.save(session.id, agent.messages);
      res.json({ sessionId: session.id, reply: result.toString() });
    } catch (error) {
      console.error("[/chat] error:", error);
      res.status(500).json({ sessionId: session.id, error: String(error) });
    }
  });

  // Streaming: forward every agent event as an SSE message with an event id.
  app.post("/chat/stream", async (req: Request, res: Response) => {
    const parsed = parseChatBody(req.body as ChatBody);
    if (!parsed) {
      res.status(400).json({ error: "Body must include a non-empty 'message' string." });
      return;
    }

    const session = sessions.getOrCreate(parsed.sessionId);
    const agent: Agent = buildAgent({ session, sessions, mcpTools });

    // SSE headers.
    res.writeHead(200, {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    });

    let eventId = 0;
    const send = (event: string, data: unknown): void => {
      eventId += 1;
      res.write(`id: ${eventId}\n`);
      res.write(`event: ${event}\n`);
      res.write(`data: ${JSON.stringify(data)}\n\n`);
    };

    // Tell the client which session this stream belongs to.
    send("session", { sessionId: session.id });

    // If the client disconnects, cancel the in-flight agent run.
    req.on("close", () => {
      agent.cancel?.();
    });

    try {
      for await (const streamEvent of agent.stream(parsed.message)) {
        // Every AgentStreamEvent has a `type` and a wire-safe `toJSON()`.
        send(streamEvent.type, streamEvent);
      }
      sessions.save(session.id, agent.messages);
      send("done", { sessionId: session.id });
    } catch (error) {
      console.error("[/chat/stream] error:", error);
      send("error", { message: String(error) });
    } finally {
      res.end();
    }
  });

  return { app, sessions };
}
