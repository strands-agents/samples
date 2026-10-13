/**
 * In-memory session store.
 *
 * Keeps a per-session conversation history (an array of Strands `Message`
 * objects) plus lightweight metadata used by the rate-limit intervention.
 * The history is fed back into the agent on every turn so the chatbot is
 * stateful across requests.
 *
 * This is intentionally simple and process-local. For production, back this
 * with a shared store (Redis, DynamoDB, the SDK's `SessionManager`, etc.).
 */

import { randomUUID } from "node:crypto";
import type { Message } from "@strands-agents/sdk";

export interface Session {
  /** Stable session identifier. */
  id: string;
  /** Full conversation history replayed into the agent each turn. */
  messages: Message[];
  /** Epoch ms when the session was created. */
  createdAt: number;
  /** Epoch ms of the most recent activity. */
  lastActiveAt: number;
  /** Timestamps (epoch ms) of recent tool calls, for rate limiting. */
  toolCallTimestamps: number[];
}

export class SessionStore {
  private readonly sessions = new Map<string, Session>();

  /**
   * Return the session for `id`, creating a fresh one when it does not exist
   * or when `id` is omitted. Always returns a usable session.
   */
  getOrCreate(id?: string): Session {
    if (id) {
      const existing = this.sessions.get(id);
      if (existing) {
        existing.lastActiveAt = Date.now();
        return existing;
      }
    }

    const now = Date.now();
    const session: Session = {
      id: id ?? randomUUID(),
      messages: [],
      createdAt: now,
      lastActiveAt: now,
      toolCallTimestamps: [],
    };
    this.sessions.set(session.id, session);
    return session;
  }

  /** Look up a session without creating one. */
  get(id: string): Session | undefined {
    return this.sessions.get(id);
  }

  /** Persist the conversation history for a session after a turn completes. */
  save(id: string, messages: Message[]): void {
    const session = this.sessions.get(id);
    if (!session) return;
    session.messages = messages;
    session.lastActiveAt = Date.now();
  }

  /** Record a tool call timestamp for rate-limit accounting. */
  recordToolCall(id: string, at: number = Date.now()): void {
    const session = this.sessions.get(id);
    if (!session) return;
    session.toolCallTimestamps.push(at);
  }

  /** Delete a session. Returns true when a session was removed. */
  delete(id: string): boolean {
    return this.sessions.delete(id);
  }

  /** Number of live sessions (useful for a health endpoint). */
  get size(): number {
    return this.sessions.size;
  }
}
