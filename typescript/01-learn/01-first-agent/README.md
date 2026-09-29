# Getting started with Strands Agents (TypeScript)

Strands Agents is an open source SDK that takes a model-driven approach to building AI agents in just a few lines of code. This quickstart guide will walk you through creating your first agent in TypeScript using large language models to handle planning and tool usage autonomously.


## Prerequisites

- Node.js 22 or later (required by `@strands-agents/sdk`)
- AWS credentials configured with access to Amazon Bedrock, and the model enabled in your region
- Basic understanding of TypeScript/JavaScript programming

## Creating Your First Agent

![Agent Architecture](images/simple_agent.png)

| Feature | Description |
|---------|-------------|
| Agent Structure | Single agent architecture |

The example in `src/firstAgent.ts` demonstrates how to:

- Create a basic agent with the Claude Sonnet 4.6 model from Amazon Bedrock
- Configure the agent with a system prompt
- Invoke the agent with a message
- Stream the response to the console

## Running the Example

```bash
cd typescript/01-learn/01-first-agent
npm install
npx tsx src/firstAgent.ts
```

To use a different Bedrock model or inference profile, set `MODEL_ID`:

```bash
MODEL_ID=us.anthropic.claude-haiku-4-5-20251001-v1:0 npx tsx src/firstAgent.ts
```


## Additional Resources

- [Strands Agents Documentation](https://strandsagents.com/latest/)



