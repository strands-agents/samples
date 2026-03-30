/**
 * Invokes a deployed Amazon Bedrock AgentCore Runtime with a prompt.
 *
 * Uses the InvokeAgentRuntimeCommand to send requests to deployed agents.
 * Each invocation creates a unique session for isolated execution.
 *
 * Usage: AGENT_RUNTIME_ARN=<arn> npm run invoke "your prompt"
 *
 */
import { BedrockAgentCoreClient, InvokeAgentRuntimeCommand } from '@aws-sdk/client-bedrock-agentcore';
import { randomBytes } from 'crypto';

// Main invocation flow:
// 1. Parse configuration from environment variables and command line
// 2. Validate required parameters
// 3. Create client and prepare the invocation command
// 4. Send request and handle response

// Step 1: Parse configuration from environment and command line
const AGENT_RUNTIME_ARN = process.env.AGENT_RUNTIME_ARN;
const REGION = process.env.AWS_REGION || 'us-east-1';
const PROMPT = process.argv[2] || 'What is the weather now?';

// Step 2: Validate required parameters
if (!AGENT_RUNTIME_ARN) {
  console.error('AGENT_RUNTIME_ARN environment variable is required');
  process.exit(1);
}

// Step 3: Create client and prepare the invocation command
const client = new BedrockAgentCoreClient({ region: REGION });
const sessionId = randomBytes(17).toString('hex');

const command = new InvokeAgentRuntimeCommand({
  agentRuntimeArn: AGENT_RUNTIME_ARN,
  runtimeSessionId: sessionId,
  payload: new TextEncoder().encode(PROMPT),
  qualifier: 'DEFAULT'
});

// Step 4: Send request and handle response
try {
  const response = await client.send(command);
  const responseBody = await response.response?.transformToString();
  console.log('Agent Response:', responseBody);
} catch (error) {
  console.error('Invocation failed:', error);
  process.exit(1);
}
