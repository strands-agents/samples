import {
  Agent,
  BedrockModel,
  BeforeToolCallEvent,
  MessageAddedEvent,
} from "@strands-agents/sdk";
import { calculator } from "./tools";

const main = async () => {
  const model = new BedrockModel({
    modelId: "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
  });

  const agent = new Agent({
    model,
    tools: [calculator],
    printer: false,
  });
  agent.hooks.addCallback(MessageAddedEvent, (e) => {
    console.log(`MODEL OUTPUT: ${JSON.stringify(e.message.content)}`);
  });

  agent.hooks.addCallback(BeforeToolCallEvent, (e) => {
    console.log(`USING TOOL: ${e.toolUse.name}`);
  });

  // invoke the agent
  await agent.invoke("Calculate 2+2");
};

main();
