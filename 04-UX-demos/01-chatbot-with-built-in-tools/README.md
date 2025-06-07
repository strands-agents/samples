# Strands Chatbot with Built-in Tools

A web-based chat interface for the Strands Agent framework, providing a conversational AI experience with configurable tools.

## Overview

This project demonstrates how to build a web application that leverages the Strands Agents framework to create an interactive chatbot with configurable built-in tools. The application includes:

- A FastAPI backend that integrates with Strands Agents
- A responsive web interface for chatting with the AI
- Real-time metrics and performance monitoring
- Configurable tool selection for the AI agent
- User session persistence

## Project Structure

```
01-chatbot-with-built-in-tools/
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
    └── ...                   # AWS CDK deployment code
```

## Features

- **Interactive Chat Interface**: Clean, responsive design for conversing with the AI
- **Tool Configuration**: Select which Strands tools the AI can use during conversations
- **Performance Metrics**: Real-time display of:
  - Latency measurements
  - Token usage statistics
  - Tool execution metrics
  - Agent cycle information
- **User Sessions**: Persistent conversations across page reloads
- **Customizable System Prompt**: Modify the AI's behavior through system prompt configuration

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

```bash
cd app
docker build -t strands-chatbot .
docker run -p 8003:8003 -e AWS_REGION=us-west-2 strands-chatbot
```

### AWS Deployment

Deploy to AWS using the provided CDK code:

```bash
cd infra
npm install
npm run build
cdk deploy
```

## Usage Examples

### Basic Conversation
Start a conversation with the AI by typing in the chat input field. The AI will respond based on its configured system prompt and available tools.

### Configuring Tools
1. Click on the "Tools" panel on the right side
2. Select or deselect tools from the list
3. Click "Update" to apply changes
4. The AI will now use only the selected tools in future conversations

### Viewing Performance Metrics
The "Metrics Summary" panel displays:
- Total cycles and average cycle time
- Tool usage statistics including call count and success rate
- Token usage (input, output, and total)
- Total latency measurements

## Customization

### Modifying the System Prompt
1. Enter a new system prompt in the settings panel
2. Click "Set System Prompt" to apply changes
3. The AI's behavior will update according to the new instructions

### Adding New Tools
To add custom tools, modify the `available_tools` dictionary in `main.py` and add your tool implementation.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.