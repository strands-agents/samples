/**
 * Creates or updates an Amazon Bedrock AgentCore Runtime from a containerized agent image.
 * Uses CloudFormation stack outputs to get the IAM role and ECR repository URI.
 *
 */
import { BedrockAgentCoreControlClient, CreateAgentRuntimeCommand, UpdateAgentRuntimeCommand, ListAgentRuntimesCommand, GetAgentRuntimeCommand } from '@aws-sdk/client-bedrock-agentcore-control';
import { CloudFormationClient, DescribeStacksCommand } from '@aws-sdk/client-cloudformation';

// Get the region, stack name, and agent name from the environment variables
const REGION = process.env.AWS_REGION || 'us-east-1';
const STACK_NAME = process.env.STACK_NAME || 'agentcore-prerequisites';
const AGENT_NAME = 'agentcore_deployment';

// Create the CloudFormation and AgentCore clients
const cfnClient = new CloudFormationClient({ region: REGION });
const agentCoreClient = new BedrockAgentCoreControlClient({ region: REGION });

// Get the IAM role and ECR repository URI from the prerequisites CloudFormation stack
async function getStackOutputs() {
  const command = new DescribeStacksCommand({ StackName: STACK_NAME });
  const response = await cfnClient.send(command);
  const outputs = response.Stacks?.[0]?.Outputs || [];

  return {
    roleArn: outputs.find(o => o.OutputKey === 'RoleArn')?.OutputValue,
    repositoryUri: outputs.find(o => o.OutputKey === 'RepositoryUri')?.OutputValue
  };
}

// Check if the agent already exists for idempotent deployments (update if exists, create if not)
async function findExistingAgent() {
  const command = new ListAgentRuntimesCommand({});
  const response = await agentCoreClient.send(command);
  return (response.agentRuntimes || []).find((a) => a.agentRuntimeName === AGENT_NAME);
}

// Poll until the runtime reaches READY status or fails
async function waitForReady(agentRuntimeId: string) {
  let status: string | undefined;
  do {
    await new Promise(r => setTimeout(r, 10000)); // 10 sec
    const res = await agentCoreClient.send(new GetAgentRuntimeCommand({ agentRuntimeId }));
    status = res.status;
    console.log(`  Status: ${status}`);
    if (status === 'CREATE_FAILED' || status === 'UPDATE_FAILED') {
      throw new Error(`Deployment failed: ${res.failureReason || 'Unknown'}`);
    }
  } while (status === 'CREATING' || status === 'UPDATING');
  return status;
}

// Main deployment flow:
// 1. Fetch infrastructure details (IAM role, ECR URI) from CloudFormation
// 2. Check if an agent with this name already exists
// 3. Update the existing agent or create a new one
try {
  // Step 1: Get required infrastructure from CloudFormation stack outputs
  console.log('Fetching CloudFormation stack outputs...');
  const { roleArn, repositoryUri } = await getStackOutputs();

  if (!roleArn || !repositoryUri) {
    throw new Error('Missing required CloudFormation outputs. Deploy prerequisites.yaml first.');
  }

  console.log(`Role ARN: ${roleArn}`);
  console.log(`Repository URI: ${repositoryUri}`);

  // Step 2: Check for existing agent to determine create vs update
  const existingAgent = await findExistingAgent();

  // Step 3: Deploy - update existing or create new agent runtime
  if (existingAgent) {
    // Update existing runtime with new container image
    console.log(`\nUpdating existing AgentCore Runtime: ${existingAgent.agentRuntimeId}`);
    const command = new UpdateAgentRuntimeCommand({
      agentRuntimeId: existingAgent.agentRuntimeId,
      agentRuntimeArtifact: {
        containerConfiguration: {
          containerUri: `${repositoryUri}:latest`
        }
      },
      roleArn,
      networkConfiguration: { networkMode: 'PUBLIC' }
    });

    const response = await agentCoreClient.send(command);
    console.log('Waiting for runtime to be ready...');
    await waitForReady(response.agentRuntimeId!);
    console.log('\n✓ Agent Runtime updated and READY!');
    console.log(`Agent Runtime ARN: ${response.agentRuntimeArn}`);
    console.log('\nTo invoke:');
    console.log(`AGENT_RUNTIME_ARN=${response.agentRuntimeArn} npm run invoke "your prompt"`);
  } else {
    // Create new runtime with container URI, IAM role, and network configuration
    console.log('\nCreating AgentCore Runtime...');
    const command = new CreateAgentRuntimeCommand({
      agentRuntimeName: AGENT_NAME,
      agentRuntimeArtifact: {
        containerConfiguration: {
          containerUri: `${repositoryUri}:latest`
        }
      },
      networkConfiguration: { networkMode: 'PUBLIC' },
      roleArn
    });

    const response = await agentCoreClient.send(command);
    console.log('Waiting for runtime to be ready...');
    await waitForReady(response.agentRuntimeId!);
    console.log('\n✓ Agent Runtime created and READY!');
    console.log(`Agent Runtime ARN: ${response.agentRuntimeArn}`);
    console.log('\nTo invoke:');
    console.log(`AGENT_RUNTIME_ARN=${response.agentRuntimeArn} npm run invoke "your prompt"`);
  }
} catch (error) {
  console.error('Deployment failed:', error);
  process.exit(1);
}
