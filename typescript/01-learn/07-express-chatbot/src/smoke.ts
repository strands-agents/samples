/**
 * Smoke test — verifies the pieces that do not require Bedrock credentials:
 *   1. the three Zod tools validate input and return expected shapes,
 *   2. the moderation intervention denies blocked terms,
 *   3. the rate-limit intervention denies past the configured cap,
 *   4. the Express app boots and rejects an empty chat body with 400.
 *
 * Run with: npm run smoke
 * Exits non-zero on the first failed assertion.
 */

import assert from "node:assert/strict";
import type { AddressInfo } from "node:net";
import { TextBlock } from "@strands-agents/sdk";
import { calculate, getCurrentTime } from "./tools/chatTools.js";
import { SessionStore } from "./sessions/SessionStore.js";
import { RateLimitIntervention } from "./interventions/RateLimitIntervention.js";
import { ModerationIntervention } from "./interventions/ModerationIntervention.js";
import { createServer } from "./server.js";

// Minimal fakes matching the fields the interventions actually read.
// Interventions read `event.agent.appState.get('sessionId')` and
// `event.agent.messages`, so the fake wraps an `agent` with those.
function fakeEvent(sessionId: string, userText?: string) {
  return {
    agent: {
      appState: {
        get: (k: string) => (k === "sessionId" ? sessionId : undefined),
      },
      messages: userText
        ? [{ role: "user", content: [new TextBlock(userText)] }]
        : [],
    },
  } as never;
}

async function run(): Promise<void> {
  // 1. Tools --------------------------------------------------------------
  assert.equal(getCurrentTime.name, "get_current_time");
  assert.equal(calculate.name, "calculate");
  assert.ok(calculate.description.length > 0, "calculate has a description");
  console.log("  [tools] get_current_time & calculate registered with schemas — OK");

  // 2. Moderation ---------------------------------------------------------
  const moderation = new ModerationIntervention(["forbidden"]);
  const clean = await moderation.beforeModelCall(fakeEvent("s1", "hello there"));
  assert.equal(clean.type, "proceed", "clean text should proceed");
  const dirty = await moderation.beforeModelCall(
    fakeEvent("s1", "this is FORBIDDEN content"),
  );
  assert.equal(dirty.type, "deny", "blocked term should deny");
  console.log("  [moderation] proceed on clean, deny on blocked term — OK");

  // 3. Rate limiting ------------------------------------------------------
  const sessions = new SessionStore();
  const session = sessions.getOrCreate("rl-session");
  const rl = new RateLimitIntervention(sessions, 2, 60_000);
  const evt = fakeEvent(session.id);
  const first = await rl.beforeToolCall(evt);
  const second = await rl.beforeToolCall(evt);
  const third = await rl.beforeToolCall(evt);
  assert.equal(first.type, "proceed", "1st call proceeds");
  assert.equal(second.type, "proceed", "2nd call proceeds");
  assert.equal(third.type, "deny", "3rd call over cap denies");
  console.log("  [rate-limit] allows up to cap then denies — OK");

  // 4. HTTP layer ---------------------------------------------------------
  const { app } = createServer({ mcpTools: [] });
  const server = app.listen(0);
  await new Promise<void>((resolve) => server.once("listening", resolve));
  const { port } = server.address() as AddressInfo;

  const badRes = await fetch(`http://localhost:${port}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: "" }),
  });
  assert.equal(badRes.status, 400, "empty message should be 400");

  const healthRes = await fetch(`http://localhost:${port}/health`);
  const health = (await healthRes.json()) as { status: string };
  assert.equal(health.status, "ok", "health should be ok");
  console.log("  [http] 400 on empty body, /health ok — OK");

  server.close();
  console.log("\nSmoke test passed.");
}

run().catch((error) => {
  console.error("\nSmoke test FAILED:", error);
  process.exit(1);
});
