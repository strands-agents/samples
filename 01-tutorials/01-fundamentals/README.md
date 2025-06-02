# Fundamentals

This folder contains a series of tutorials covering the fundamental concepts of building AI agents with AWS Strands. Each tutorial builds upon the previous one, introducing key concepts and features to help you create sophisticated AI agents.

## Structure

| Example | Description                                                                  | Features showcased                                                                                   |
|---------|------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| F1      | [Creating First Strands Agent](./01-first-agent)                             | Agent initialization, usage of a default tool, creation of custom tools                              |
| F2      | [Model Providers - Ollama](./02-model-providers/01-ollama-model)             | Create agent with Ollama model                                                                       |
| F2      | [Model Providers - OpenAI](./02-model-providers/02-openai-model)             | Create agent with GPT 4.0 as model                                                                   |
| F3      | [Connecting with AWS services](./03-connecting-with-aws-services)            | Connecting to Amazon Bedrock Knowledge Base and Amazon DynamoDB                                      |
| F4      | [Tools - Using MCP tools](./04-tools/01-using-mcp-tools)                     | Integrating MCP tool calling to your agent                                                           |
| F4      | [Tools - Custom Tools](./04-tools/02-custom-tools)                           | Creating and using custom tools with your agent                                                      |
| F5      | [Streaming response from agent](./05-streaming-agent-response)               | Streaming your agent's response using Async Iterators or Callbacks (Stream Handlers)                 |
| F6      | [Integrating Bedrock Guardrail](./06-guardrail-integration)                  | Integrate an Amazon Bedrock Guardrail to your agent                                                  |
| F7      | [Adding memory to your agent](./07-memory-persistent-agents)                 | Personal assistant using memory and websearch tools                                                  |
| F8      | [Observability and Evaluation](./08-observability-and-evaluation)            | Adding observability and evaluation to your agent                                                    |
