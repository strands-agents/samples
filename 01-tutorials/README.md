# Getting started with Strands SDK

In this folder we will provide Jupyter Notebook examples on how to get started with different Strands Agents functionalities.

## Fundamentals
| Example | Description                                                                        | Features showcased                                                                                   |
|---------|------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| F1      | [Creating First Strands Agent](01-fundamentals/01-first-agent)                     | Agent initialization, usage of a default tool, creation of custom tools                              |
| F2      | [Model Providers - OpenAI](01-fundamentals/02-model-providers/02-openai-model)     | Create agent with GPT 4.0 as model                                                                   |
| F2      | [Model Providers - Ollama](01-fundamentals/02-model-providers/01-ollama-model)     | Create agent with Ollama model                                                                       |
| F3      | [Connecting with AWS services](01-fundamentals/03-connecting-with-aws-services)    | Connecting to Amazon Bedrock Knowledge Base and Amazon DynamoDB                                      |
| F4      | [Tools - Using MCP tools](01-fundamentals/04-tools/01-using-mcp-tools)                     | Integrating MCP tool calling to your agent                                                           |
| F4      | [Tools - Custom Tools](01-fundamentals/04-tools/02-custom-tools)                           | Creating and using custom tools with your agent                                                      |
| F5      | [Streaming response from agent](01-fundamentals/05-streaming-agent-response)       | Streaming your agent's response using Async Iterators or Callbacks (Stream Handlers)                 |
| F6      | [Integrating Bedrock Guardrail](01-fundamentals/06-guardrail-integration)          | Integrate an Amazon Bedrock Guardrail to your agent                                                  |
| F7      | [Adding memory to your agent](01-fundamentals/07-memory-persistent-agents)         | Personal assistant using memory and websearch tools                                                  |
| F8     | [Observability and Evaluation](01-fundamentals/08-observability-and-evaluation)    | Adding observability and evaluation to your agent                                                    |
| F9     | [Bidirectional Streaming](01-fundamentals/09-bidirectional-streaming)    | Bidirectional streaming agent enable realtime voice chat
| F10     | [Human in the loop](01-fundamentals/10-human-in-the-loop)    | Interrupt your agent's loop for human approval

## Multi-Agent Systems
| Example | Description                                                | Features showcased                                                                                   |
|---------|------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| M1      | [Using Agent as tool](02-multi-agent-systems/01-agent-as-tool) | Create a multi-agent collaboration example using an agent as tool                                |
| M2      | [Creating a Swarm Agent](02-multi-agent-systems/02-swarm-agent) | Create a multi-agent system consisting of multiple AI agents working together                   |
| M3      | [Creating a Graph Agent](02-multi-agent-systems/03-graph-agent) | Create a structured network of specialized AI agents with defined communication patterns         |

## Deployment
| Example | Description                                                      | Features showcased                                                                              |
|---------|------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| D1      | [AWS Lambda Deployment](03-deployment/01-lambda-deployment)       | Deploying your agent to an AWS Lambda Function                                                  |
| D2      | [AWS Fargate Deployment](03-deployment/02-fargate-deployment)     | Deploying your agent to AWS Fargate                                                             |