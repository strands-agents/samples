/*
  A simple streaming Express server.  Test with the following:
  
  curl -X POST --no-buffer -H "Content-Type: application/json" \
  -d '{"prompt": "What is weather in NYC?"}' \
  http://127.0.0.1:8001/stream

 */
import { Agent, BedrockModel } from "@strands-agents/sdk";
import express from "express";
import { weatherForecast } from "./tools";

const port = 8001;

type ValidRequest = {
  prompt: string;
};

const isValidRequest = (req: any): req is ValidRequest => {
  const input = req as ValidRequest;
  if (
    input.prompt !== undefined &&
    typeof input.prompt === "string" &&
    input.prompt.length <= 256
  ) {
    return true;
  }
  return false;
};

const main = async () => {
  const app = express();
  app.use(express.json());

  const model = new BedrockModel({
    modelId: "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
  });

  app.post("/stream", async (req, res) => {
    res.setHeader("Content-Type", "text/plain");
    res.setHeader("Transfer-Encoding", "chunked"); // Indicate chunked transfer

    if (!req.body) {
      res.status(400).end("No input");
      return;
    }
    const input = req.body;

    if (
      !isValidRequest(input) &&
      req.headers["content-type"] === "application/json"
    ) {
      res.status(400).end("Bad input");
    } else {
      const agent = new Agent({
        model,
        tools: [weatherForecast],
        printer: false,
      });

      // invoke the agent
      const eventStream = agent.stream(input.prompt);
      try {
        for await (const ev of eventStream) {
          if (ev.type === "textBlock") {
            res.write(ev.text.toString());
          }
        }
        res.end();
      } catch (error) {
        console.error("Streaming error: ", error);
        res.status(500).end("Error during streaming");
      }
    }
  });

  app.listen(port, () => {
    console.log(`✅ Server is running at http://127.0.0.1:${port}`);
  });
};

main();
