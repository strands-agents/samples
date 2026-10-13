/**
 * RateLimitIntervention — caps how many tool calls a single session may make
 * within a sliding time window.
 *
 * Implemented as a Strands `InterventionHandler` that overrides `beforeToolCall`.
 * On each tool call it prunes timestamps older than the window, and if the
 * session is already at the limit it returns `deny(...)`, which blocks the
 * tool and feeds the reason back to the model so it can respond gracefully.
 *
 * State is read from the agent: the server stores `sessionId` in agent state,
 * and the shared `SessionStore` holds the per-session tool-call timestamps.
 */

import {
  InterventionHandler,
  InterventionActions,
  type BeforeToolCallEvent,
} from "@strands-agents/sdk";
import type { SessionStore } from "../sessions/SessionStore.js";

export class RateLimitIntervention extends InterventionHandler {
  readonly name = "rate-limit";
  /** A broken policy check should fail closed rather than let calls through. */
  override readonly onError = "deny" as const;

  constructor(
    private readonly sessions: SessionStore,
    private readonly maxToolCalls: number,
    private readonly windowMs: number,
  ) {
    super();
  }

  override beforeToolCall(
    event: BeforeToolCallEvent,
  ):
    | ReturnType<typeof InterventionActions.proceed>
    | ReturnType<typeof InterventionActions.deny> {
    const sessionId = event.agent.appState.get("sessionId") as string | undefined;
    if (!sessionId) {
      // No session context — allow, nothing to meter against.
      return InterventionActions.proceed();
    }

    const session = this.sessions.get(sessionId);
    if (!session) {
      return InterventionActions.proceed();
    }

    const now = Date.now();
    const windowStart = now - this.windowMs;

    // Drop timestamps outside the current window.
    session.toolCallTimestamps = session.toolCallTimestamps.filter(
      (ts) => ts > windowStart,
    );

    if (session.toolCallTimestamps.length >= this.maxToolCalls) {
      const retryInSec = Math.ceil(
        (session.toolCallTimestamps[0]! + this.windowMs - now) / 1000,
      );
      return InterventionActions.deny(
        `Rate limit reached: at most ${this.maxToolCalls} tool call(s) per ` +
          `${Math.round(this.windowMs / 1000)}s per session. ` +
          `Try again in about ${retryInSec}s. Answer from what you already know if possible.`,
      );
    }

    // Count this call and allow it.
    session.toolCallTimestamps.push(now);
    return InterventionActions.proceed();
  }
}
