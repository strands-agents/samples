// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * Agent Proxy - Forwards AG-UI protocol requests to the local Strands agent.
 * 
 * This proxy:
 * 1. Returns agent info on GET (for CopilotKit discovery)
 * 2. Forwards POST requests to the agent with proper AG-UI format
 */

import { NextRequest, NextResponse } from "next/server";
import { randomUUID } from "crypto";

const AGENT_URL = process.env.AGENT_URL || "http://localhost:8001";

// GET /api/agent-proxy - Return agent info for CopilotKit discovery
export const GET = async () => {
  console.log("=== GET /api/agent-proxy ===");
  
  return NextResponse.json({
    agents: [{
      name: "strands_agent",
      description: "AgentCore documentation assistant with AG-UI features",
    }],
  });
};

// POST /api/agent-proxy - Forward to agent
export const POST = async (req: NextRequest) => {
  console.log("=== POST /api/agent-proxy ===");
  
  try {
    console.log("Forwarding to:", AGENT_URL);

    const rawBody = await req.text();
    console.log("Raw body preview:", rawBody.substring(0, 300));

    // Parse the incoming body
    let parsedBody: any;
    try {
      parsedBody = JSON.parse(rawBody);
    } catch {
      parsedBody = {};
    }

    // Ensure messages have required 'id' field (AG-UI protocol requirement)
    const messages = (parsedBody.messages || []).map((msg: any) => ({
      ...msg,
      id: msg.id || randomUUID(),
    }));

    // Ensure AG-UI required fields are present
    const aguiPayload: any = {
      threadId: parsedBody.threadId || randomUUID(),
      runId: parsedBody.runId || randomUUID(),
      messages,
      tools: parsedBody.tools || [],
      context: parsedBody.context || [],
      state: parsedBody.state || {},
      forwardedProps: parsedBody.forwardedProps || {},
    };

    console.log("AG-UI payload threadId:", aguiPayload.threadId);
    console.log("AG-UI payload messages count:", aguiPayload.messages?.length);

    const response = await fetch(AGENT_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(aguiPayload),
    });

    console.log("Agent response status:", response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Agent error:", errorText);
      return new NextResponse(errorText, { 
        status: response.status,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Pass through the SSE stream directly
    return new NextResponse(response.body, {
      status: response.status,
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    console.error("Proxy error:", error);
    return NextResponse.json(
      { error: String(error) }, 
      { status: 500 }
    );
  }
};
