import {
  Agent,
  AgentResult,
  AgentStreamEvent,
  BedrockModel,
} from "@strands-agents/sdk";
import { calculator } from "./tools";

const processStreamingResponse = async (
  eventStream: AsyncGenerator<AgentStreamEvent, AgentResult, undefined>
) => {
  for await (const event of eventStream) {
    if (event.type === "toolUseBlock") {
      console.log(
        `🔧 Using tool: ${event.name}, input: ${JSON.stringify(event.input)}`
      );
    } else if (event.type === "textBlock") {
      console.log(`📟 Text: ${event.text}`);
    }
  }
};

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
  await processStreamingResponse(eventStream);
};

main();
