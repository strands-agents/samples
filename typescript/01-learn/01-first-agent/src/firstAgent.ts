/**
 * First Agent - Getting Started with Strands Agents
 *
 * This example demonstrates how to create and invoke a simple agent.
 */

import { Agent, BedrockModel } from "@strands-agents/sdk";

async function main() {
    // Create an agent backed by Amazon Bedrock. The model is pinned so the sample
    // behaves the same when the SDK's default model changes; override it with MODEL_ID.
    const agent = new Agent({
        model: new BedrockModel({
            modelId: process.env.MODEL_ID ?? "global.anthropic.claude-sonnet-4-6",
        }),
        systemPrompt: "You are a helpful assistant that provides concise responses."
    });

    // Send a message to the agent. The agent streams its reply to the console
    // as it is generated, so there is no need to print the result again.
    await agent.invoke("Hello! Tell me a joke.");
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
