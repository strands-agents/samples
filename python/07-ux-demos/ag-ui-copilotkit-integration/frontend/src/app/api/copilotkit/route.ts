// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * CopilotKit API Route - Connects to the Strands agent via AG-UI protocol.
 * 
 * For local development: Points to local agent proxy
 * For AgentCore Runtime: Points to agentcore-proxy which handles IAM auth
 */

import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";

// Determine agent URL based on environment
function getAgentUrl(): string {
  // Always use the proxy - it handles message formatting for AG-UI protocol
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3001';
  console.log("Using agent proxy at:", `${baseUrl}/api/agent-proxy`);
  return `${baseUrl}/api/agent-proxy`;
}

// Create runtime with the Strands agent
const agentUrl = getAgentUrl();
const runtime = new CopilotRuntime({
  agents: {
    strands_agent: new HttpAgent({ url: agentUrl }),
  },
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new ExperimentalEmptyAdapter(),
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
