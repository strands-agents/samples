/**
 * Entry point.
 *
 * Loads `.env` (if present), optionally connects to an MCP server, starts the
 * Express app, and wires graceful shutdown that disconnects MCP cleanly.
 */

import { existsSync } from "node:fs";
import { config } from "./config.js";
import { createServer } from "./server.js";
import { connectMcp } from "./mcp/mcpTools.js";

// Load environment variables from a local .env file when available.
// Node 20.6+ ships process.loadEnvFile; guarded so it is optional.
if (existsSync(".env") && typeof process.loadEnvFile === "function") {
  process.loadEnvFile(".env");
}

async function main(): Promise<void> {
  const mcp = await connectMcp();
  if (!mcp) {
    console.log("[mcp] no MCP_SERVER_URL configured — running with local tools only.");
  }

  const { app } = createServer({ mcpTools: mcp?.tools ?? [] });

  const server = app.listen(config.port, () => {
    console.log(`Chatbot server listening on http://localhost:${config.port}`);
    console.log(`  POST /chat          (JSON reply)`);
    console.log(`  POST /chat/stream   (SSE stream)`);
    console.log(`  GET  /health`);
  });

  const shutdown = async (signal: string): Promise<void> => {
    console.log(`\n[${signal}] shutting down...`);
    server.close();
    if (mcp) {
      await mcp.disconnect().catch(() => undefined);
    }
    process.exit(0);
  };

  process.on("SIGINT", () => void shutdown("SIGINT"));
  process.on("SIGTERM", () => void shutdown("SIGTERM"));
}

main().catch((error) => {
  console.error("Fatal error during startup:", error);
  process.exit(1);
});
