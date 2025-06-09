# Strands Playground

A web-based interactive playground for experimenting with the Strands SDK, allowing users to quickly test and prototype AI agents with configurable tools.

## Overview

This project provides a sandbox environment for developers to experiment with the Strands Agents framework. The playground allows you to:

- Interact with AI agents powered by Strands SDK
- Configure and test different combinations of Strands tools
- Customize model parameters and system prompts
- Visualize agent performance metrics
- Persist conversations across sessions
- Experiment with code and file operations through the agent

## Project Structure

```
strands-playground/
├── app/                      # Application code
│   ├── static/               # Frontend assets
│   │   ├── app.js            # Main application logic
│   │   ├── index.html        # HTML interface
│   │   ├── styles.css        # CSS styling
│   │   ├── summary-panel.js  # Metrics visualization
│   │   └── tools-panel.js    # Tool selection interface
│   ├── Dockerfile            # Container definition
│   ├── main.py               # FastAPI backend
│   └── requirements.txt      # Python dependencies
└── infra/                    # Infrastructure as code
    ├── lib/                  # CDK stack definition
    ├── bin/                  # CDK entry point
    └── ...                   # AWS CDK deployment code
```

## Features

- **Interactive Playground Interface**: Clean, responsive design for experimenting with Strands agents
- **Comprehensive Tool Selection**: Access to 25+ Strands tools including:
  - File operations (read/write)
  - AWS service integration
  - Python REPL execution
  - HTTP requests
  - Image generation
  - Calculator
  - Shell commands
  - And many more
- **Tool Configuration**: Select which Strands tools the agent can use during experiments
- **Performance Metrics**: Real-time display of:
  - Latency measurements
  - Token usage statistics
  - Tool execution metrics
  - Agent cycle information
- **User Sessions**: Persistent conversations across page reloads
- **Customizable System Prompt**: Modify the agent's behavior through system prompt configuration
- **Model Parameter Tuning**: Configure Bedrock model settings including:
  - Model ID
  - Region
  - Max tokens
  - Temperature
  - Top P

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 14+ (for CDK deployment)
- AWS credentials configured (for AWS Bedrock access)

### Local Development

1. Install Python dependencies:
   ```bash
   cd app
   pip install -r requirements.txt
   ```

2. Run the FastAPI server:
   ```bash
   cd app
   python main.py
   ```

3. Open your browser and navigate to `http://localhost:8003`

### Docker Deployment

Build and run the application using Docker:

#### With Local File-Based Session Management
```bash
cd app
docker build -t strands-playground .
docker run -p 8003:8003 strands-playground
```

#### With DynamoDB Session Management
```bash
cd app
docker build -t strands-playground .
docker run -p 8003:8003 -e TABLE_NAME="strands_playground_session" -e TABLE_REGION="us-west-2" -e PRIMARY_KEY="SessionId" strands-playground
```

### AWS Deployment

Deploy to AWS using the provided CDK code:

```bash
cd infra
npm install
npm run build
cdk deploy
```

The CDK deployment creates the following AWS resources:

- **VPC**: A Virtual Private Cloud with public and private subnets
- **VPC Endpoint**: For Amazon Bedrock Runtime access
- **ECS Cluster**: To host the containerized application
- **DynamoDB Table**: For persistent session storage
- **Fargate Service**: Running 2 instances of the application for high availability
- **Application Load Balancer**: For distributing traffic to the Fargate instances
- **IAM Roles**: With permissions for Bedrock API access
- **CloudWatch Logs**: For application logging

After deployment, the application will be accessible via the load balancer's DNS name, which is provided as an output from the CDK stack.

## Usage Examples

### Basic Experimentation
1. Enter a user ID and click "Start Session"
2. Type your prompt in the chat input field
3. The agent will respond based on its configured system prompt and available tools

### Configuring Tools
1. Use the tools panel on the left side
2. Select or deselect tools from the list
3. Click "Update" to apply changes
4. The agent will now use only the selected tools in future interactions

### Customizing Model Parameters
1. Enter the desired model ID (e.g., "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
2. Specify the AWS region (e.g., "us-west-2")
3. Optionally configure max tokens, temperature, and top P values
4. Click "Update" to apply changes

### Modifying the System Prompt
1. Enter a new system prompt in the settings panel
2. Click "Set System Prompt" to apply changes
3. The agent's behavior will update according to the new instructions

### Working with Files
To make files accessible via the web interface, instruct the agent to save them to the './static' directory. Files stored in this location will be automatically served at the root URL of the application.

## Session Management

The playground supports two methods for managing conversation sessions:

1. **Local File-Based Storage**: By default, conversations are stored in local files in a `sessions` directory.

2. **DynamoDB Storage**: For persistent storage across container restarts or in production environments, configure the following environment variables:
   - `TABLE_NAME`: Name of your DynamoDB table
   - `TABLE_REGION`: AWS region where your DynamoDB table is located
   - `PRIMARY_KEY`: Primary key name for your DynamoDB table (typically "SessionId")

## Extending the Playground

### Adding New Tools
To add custom tools, modify the `available_tools` dictionary in `main.py` and add your tool implementation along with a description in the `tool_descriptions` dictionary.

### Customizing the Frontend
The frontend is built with vanilla JavaScript and can be easily modified by editing the files in the `static` directory.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.