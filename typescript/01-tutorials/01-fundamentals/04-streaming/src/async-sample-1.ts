import { Agent, BedrockModel } from "@strands-agents/sdk";
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

  // invoke the agent
  const eventStream = agent.stream("Calculate 2+2");

  for await (const event of eventStream) {
    console.log("Event: ", event.type);
  }
};

main();
