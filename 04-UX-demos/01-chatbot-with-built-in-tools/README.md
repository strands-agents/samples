# Strands Agent Service

A web-based chat interface for the Strands Agent framework, providing a conversational AI experience using AWS Bedrock.

## Project Structure

- `backend/`: FastAPI server that handles API requests and integrates with Strands Agent
- `frontend/`: Simple HTML/CSS/JS web interface for the chat application
- `prompts/`: Text files containing system prompts for the agent
- `cdk/`: AWS CDK code for deploying the application to AWS Fargate

## Local Development

### Prerequisites

- Python 3.12+
- Node.js 14+ (for CDK deployment)
- AWS credentials configured with access to Bedrock

### Running Locally

1. Install backend dependencies:
   ```
   cd backend
   pip install -r requirements.txt
   ```

2. Run the FastAPI server:
   ```
   cd backend
   python main.py
   ```

3. Open `frontend/index.html` in your browser or serve it using a local web server.

## Docker Deployment

You can build and run the application using Docker:

```bash
# Build the Docker image
docker build -t strands-agent-service .

# Run the container
docker run -p 8003:8003 -e AWS_REGION=us-west-2 strands-agent-service
```

## AWS Fargate Deployment

The application can be deployed to AWS Fargate using the provided CDK code:

```bash
cd cdk
npm install
npm run build
cdk deploy
```

See the [CDK README](./cdk/README.md) for more detailed deployment instructions.

## Features

- Real-time chat interface
- User session persistence
- Integration with AWS Bedrock for AI capabilities
- Support for calculator and HTTP request tools
- Performance metrics display (latency and token usage)

## Configuration

The application uses AWS Bedrock's Nova Pro model by default. You can modify the model settings in `backend/main.py`.