/**
 * Express server implementing the Amazon Bedrock AgentCore Runtime HTTP Protocol Contract.
 *
 * This server hosts a Strands agent and exposes the required endpoints:
 *   - POST /invocations: Primary agent interaction endpoint (required)
 *   - GET /ping: Health check for service monitoring (required)
 *
 * The server must listen on 0.0.0.0:8080 per AgentCore container requirements.
 *
 */
import express from 'express';
import { Agent, tool, BedrockModel } from '@strands-agents/sdk';
import { z } from 'zod';

// Main server setup flow:
// 1. Configure Express server with required middleware
// 2. Define tools that extend agent capabilities
// 3. Configure the LLM model and create the agent
// 4. Implement required AgentCore endpoints (/invocations, /ping)
// 5. Start server on 0.0.0.0:8080

// Step 1: Configure Express server with middleware for handling requests
const app = express();
app.use(express.text({ type: 'application/octet-stream' }));
app.use(express.json());

// Step 2: Define tools that extend agent capabilities
const weatherTool = tool({
  name: 'weather',
  description: 'Get current weather information',
  inputSchema: z.object({
    location: z.string().optional().describe('Location to get weather for')
  }),
  callback: async () => 'sunny'
});

const calculatorTool = tool({
  name: 'calculator',
  description: 'Perform basic arithmetic operations',
  inputSchema: z.object({
    operation: z.enum(['add', 'subtract', 'multiply', 'divide']),
    a: z.number(),
    b: z.number()
  }),
  callback: async ({ operation, a, b }) => {
    switch (operation) {
      case 'add': return a + b;
      case 'subtract': return a - b;
      case 'multiply': return a * b;
      case 'divide': return b !== 0 ? a / b : 'Cannot divide by zero';
    }
  }
});

// Step 3: Configure the LLM model and create the agent
const model = new BedrockModel({
  modelId: 'us.anthropic.claude-3-5-haiku-20241022-v1:0'
});

// Configure the agent with the model, tools, and system prompt
const agent = new Agent({
  model,
  tools: [weatherTool, calculatorTool],
  systemPrompt: "You're a helpful assistant. You can tell the weather and perform calculations."
});

// Step 4: Implement required AgentCore endpoints
// POST /invocations - Primary agent interaction endpoint
// Receives incoming requests and processes them through agent logic.
app.post('/invocations', async (req, res) => {
  try {
    const userMessage = typeof req.body === 'string' ? req.body : req.body.input?.prompt;
    if (!userMessage) {
      return res.status(400).send("No prompt provided");
    }

    const result = await agent.invoke(userMessage);
    res.type('text/plain').send(result.toString());
  } catch (error) {
    res.status(500).send(`Error: ${error instanceof Error ? error.message : String(error)}`);
  }
});

// GET /ping - Health check endpoint for service monitoring and automated recovery.
// Returns {"status": "Healthy"} when ready to accept requests.
app.get('/ping', (_req, res) => {
  res.json({ status: 'Healthy' });
});

// Step 5: Start the server on 0.0.0.0:8080
const PORT = 8080;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT}`);
});
