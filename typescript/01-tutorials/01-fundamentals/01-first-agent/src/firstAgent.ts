/**
 * First Agent - Getting Started with Strands Agents
 *
 * This example demonstrates how to create and invoke a simple agent.
 */

import { Agent, BedrockModel } from "@strands-agents/sdk";

async function main() {
    // Create an agent with Amazon Bedrock model
    const agent = new Agent({
        model: new BedrockModel({
            modelId: "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        }),
        systemPrompt: "You are a helpful assistant that provides concise responses."
    });

    // Send a message to the agent
    const response = await agent.invoke("Hello! Tell me a joke.");

    // Extract and print the response text
    const messageContent = response.lastMessage.content[0];
    if (messageContent.type === 'textBlock') {
        console.log(messageContent.text);
    }
}

main().catch(console.error);
