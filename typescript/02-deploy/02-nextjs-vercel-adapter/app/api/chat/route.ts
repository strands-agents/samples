/**
 * Chat route handler — where the two SDKs meet.
 *
 * The **Vercel AI SDK owns the client**: the browser talks to this endpoint with
 * `useChat`, sending `UIMessage[]`. On the server, **Strands runs the loop**:
 * we build an `Agent` (model via `VercelModel`, tools, session, hooks) and stream
 * its events. We translate Strands stream events into the AI SDK UI message
 * stream protocol so `useChat` renders tokens and tool activity as they arrive.
 */
import {
  createUIMessageStream,
  createUIMessageStreamResponse,
  type UIMessage,
} from "ai";
import { createAgent } from "@/lib/agent";

// Strands + the AWS/AI SDKs need the Node.js runtime (not Edge).
export const runtime = "nodejs";
export const maxDuration = 60;

interface ChatRequestBody {
  messages: UIMessage[];
  /** Optional stable id so the conversation persists across requests. */
  id?: string;
}

export async function POST(req: Request): Promise<Response> {
  const { messages, id }: ChatRequestBody = await req.json();

  // Use the chat id as the Strands session id so history persists per conversation.
  const sessionId = id ?? "default-session";
  const agent = await createAgent(sessionId);

  // Strands persists its own history via the SessionManager, so we only forward
  // the latest user turn each request. Pull its text straight from the UI parts.
  const lastUser = [...messages].reverse().find((m) => m.role === "user");
  const promptText = textFromParts(lastUser?.parts);

  const stream = createUIMessageStream({
    execute: async ({ writer }) => {
      const textId = crypto.randomUUID();
      let textOpen = false;

      const openText = () => {
        if (!textOpen) {
          writer.write({ type: "text-start", id: textId });
          textOpen = true;
        }
      };
      const closeText = () => {
        if (textOpen) {
          writer.write({ type: "text-end", id: textId });
          textOpen = false;
        }
      };

      for await (const event of agent.stream(promptText)) {
        switch (event.type) {
          // Streaming model output: forward text deltas as they arrive.
          case "modelStreamUpdateEvent": {
            const inner = event.event;
            if (
              inner.type === "modelContentBlockDeltaEvent" &&
              inner.delta.type === "textDelta" &&
              inner.delta.text
            ) {
              openText();
              writer.write({
                type: "text-delta",
                id: textId,
                delta: inner.delta.text,
              });
            }
            break;
          }

          // A tool is about to run: surface it as a tool-input in the UI stream.
          case "beforeToolCallEvent": {
            closeText();
            writer.write({
              type: "tool-input-available",
              toolCallId: event.toolUse.toolUseId,
              toolName: event.toolUse.name,
              input: event.toolUse.input,
            });
            break;
          }

          // Tool finished: surface its output.
          case "afterToolCallEvent": {
            writer.write({
              type: "tool-output-available",
              toolCallId: event.toolUse.toolUseId,
              output: serializeToolResult(event.result),
            });
            break;
          }
        }
      }

      closeText();
    },
    onError: (error) => {
      console.error("[chat] stream error:", error);
      return error instanceof Error ? error.message : "Unknown error";
    },
  });

  return createUIMessageStreamResponse({ stream });
}

/** Extract plain text from a UIMessage's parts. */
function textFromParts(parts: UIMessage["parts"] | undefined): string {
  if (!parts) return "";
  return parts
    .map((part) => (part.type === "text" ? part.text : ""))
    .join("");
}

/** Flatten a Strands ToolResultBlock into a JSON-serializable value for the UI. */
function serializeToolResult(result: unknown): unknown {
  if (result && typeof result === "object" && "content" in result) {
    const content = (result as { content?: unknown }).content;
    if (Array.isArray(content)) {
      const text = content
        .map((c) =>
          c && typeof c === "object" && "text" in c
            ? String((c as { text: unknown }).text)
            : "",
        )
        .join("");
      if (text) return text;
    }
  }
  return result;
}
