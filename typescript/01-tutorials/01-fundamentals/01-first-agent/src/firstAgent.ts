/**
 * First Agent - Getting Started with Strands Agents
 *
 * This example demonstrates how to create and invoke a simple agent.
 */

import { Agent } from "@strands-agents/sdk";

async function main() {
    // Create an agent using the default model provider and model
    // Strands Agents Typescript SDK uses Amazon Bedrock as the default model provider and Claude Sonnet 4.5 as the default model
    const agent = new Agent({
        systemPrompt: "You are a helpful assistant that provides concise responses."
    });

    // Send a message to the agent
    const response = await agent.invoke("Hello! Tell me a joke.");

    // Print the response
    console.log(response.toString());
}

main().catch(console.error);
