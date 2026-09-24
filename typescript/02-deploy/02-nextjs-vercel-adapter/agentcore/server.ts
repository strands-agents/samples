/**
 * Amazon Bedrock AgentCore Runtime entrypoint.
 *
 * This is the **container path**: the same Strands agent from `lib/agent.ts`,
 * exposed over the AgentCore HTTP contract instead of a Next.js route.
 *
 *   - Host: 0.0.0.0, Port: 8080 (ARM64 container)
 *   - GET  /ping         -> health check  { "status": "Healthy" }
 *   - POST /invocations  -> agent call; streams SSE (`data: {...}` lines)
 *
 * See: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-http-protocol-contract.html
 *
 * Run locally:   npm run agentcore
 * Build image:   see agentcore/Dockerfile
 */
import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { createAgent } from "../lib/agent";

const PORT = Number(process.env.PORT ?? 8080);
const HOST = "0.0.0.0";

function readBody(req: IncomingMessage): Promise<string> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    req.on("data", (c) => chunks.push(c as Buffer));
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    req.on("error", reject);
  });
}

function sse(res: ServerResponse, data: unknown): void {
  res.write(`data: ${JSON.stringify(data)}\n\n`);
}

const server = createServer(async (req, res) => {
  // Health check.
  if (req.method === "GET" && req.url === "/ping") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "Healthy" }));
    return;
  }

  // Agent invocation (streaming).
  if (req.method === "POST" && req.url === "/invocations") {
    try {
      const raw = await readBody(req);
      const payload = raw ? (JSON.parse(raw) as { prompt?: string; sessionId?: string }) : {};
      const prompt = payload.prompt ?? "";
      const sessionId = payload.sessionId ?? "default-session";

      const agent = await createAgent(sessionId);

      res.writeHead(200, {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      });

      for await (const event of agent.stream(prompt)) {
        if (
          event.type === "modelStreamUpdateEvent" &&
          event.event.type === "modelContentBlockDeltaEvent" &&
          event.event.delta.type === "textDelta" &&
          event.event.delta.text
        ) {
          sse(res, { type: "text", text: event.event.delta.text });
        } else if (event.type === "beforeToolCallEvent") {
          sse(res, {
            type: "tool-call",
            toolName: event.toolUse.name,
            input: event.toolUse.input,
          });
        } else if (event.type === "afterToolCallEvent") {
          sse(res, { type: "tool-result", toolName: event.toolUse.name });
        }
      }

      sse(res, { type: "done" });
      res.end();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      if (!res.headersSent) {
        res.writeHead(500, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ status: "error", error: message }));
      } else {
        sse(res, { type: "error", error: message });
        res.end();
      }
    }
    return;
  }

  res.writeHead(404, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ status: "not_found" }));
});

server.listen(PORT, HOST, () => {
  console.log(`AgentCore runtime listening on http://${HOST}:${PORT}`);
});
