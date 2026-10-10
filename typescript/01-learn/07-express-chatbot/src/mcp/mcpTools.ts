/**
 * Optional MCP (Model Context Protocol) integration.
 *
 * The chatbot connects to an existing, remote MCP server over Streamable HTTP
 * at startup and loads its tools so the agent can call them alongside the
 * local Zod tools. By default `MCP_SERVER_URL` points at the public
 * AWS Knowledge MCP Server (`https://knowledge-mcp.global.api.aws`), a fully
 * managed, no-auth server that exposes up-to-date AWS documentation, code
 * samples, and official content as tools (e.g. search/read AWS docs). Set the
 * variable to any other Streamable HTTP MCP server, or leave it empty to run
 * with local tools only.
 *
 * `continueOnError: true` keeps the chatbot usable even if the MCP server is
 * unreachable — a failed connection yields an empty tool list instead of
 * crashing the process.
 */

import { McpClient } from "@strands-agents/sdk";
import { config } from "../config.js";

/** The tools returned by `McpClient.listTools()`. */
export type McpTools = Awaited<ReturnType<McpClient["listTools"]>>;

export interface McpConnection {
  client: McpClient;
  tools: McpTools;
  disconnect: () => Promise<void>;
}

/**
 * Connect to the configured MCP server and return its tools.
 * Returns `null` when no MCP server URL is configured.
 */
export async function connectMcp(): Promise<McpConnection | null> {
  const url = config.mcp.serverUrl;
  if (!url) {
    return null;
  }

  const client = new McpClient({
    url,
    applicationName: "express-strands-chatbot",
    continueOnError: true,
  });

  await client.connect();
  const tools = await client.listTools();

  console.log(
    `[mcp] connected to ${url} — loaded ${tools.length} tool(s): ` +
      tools.map((t) => t.name).join(", "),
  );

  return {
    client,
    tools,
    disconnect: () => client.disconnect(),
  };
}
