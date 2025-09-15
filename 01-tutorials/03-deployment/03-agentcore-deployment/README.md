# Amazon Bedrock AgentCore Runtime Deployment

This tutorial demonstrates how to deploy a Strands-based AI agent to Amazon Bedrock AgentCore Runtime, creating a production-ready restaurant booking system with enterprise-grade scaling and security.

## Overview

Amazon Bedrock AgentCore Runtime provides a serverless, session-isolated environment for deploying AI agents at scale. This example showcases:

- **Restaurant Booking Agent**: AI-powered assistant for restaurant reservations
- **Knowledge Base Integration**: Restaurant information and menu data
- **DynamoDB Integration**: Persistent booking storage
- **Container Deployment**: Production-ready containerization
- **IAM Security**: Least-privilege access controls

## Architecture

```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│   Client App    │───▶│  AgentCore Runtime   │───▶│  Bedrock Model  │
└─────────────────┘    └──────────────────────┘    └─────────────────┘
                                │                           │
                                ▼                           ▼
                       ┌─────────────────┐         ┌─────────────────┐
                       │   DynamoDB      │         │ Knowledge Base  │
                       │   (Bookings)    │         │ (Restaurants)   │
                       └─────────────────┘         └─────────────────┘
```

## Prerequisites

- AWS CLI configured with appropriate permissions
- Python 3.12 or later
- Docker or Podman installed and running
- Amazon Bedrock AgentCore access (preview)

### Required AWS Permissions

- Amazon Bedrock AgentCore (create/manage runtimes)
- Amazon ECR (create repositories, push images)
- IAM (create roles and policies)
- DynamoDB (create tables)
- Amazon Bedrock (Knowledge Base, model access)
- AWS Systems Manager (Parameter Store)

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r agent-requirements.txt
   ```

2. **Run the Tutorial**
   Open `deploy-agent.ipynb` in Jupyter and follow the step-by-step guide.

3. **Clean Up**
   Uncomment the cleanup section in the notebook to remove all resources.

## Project Structure

```
04-agentcore-deployment/
├── deploy-agent.ipynb          # Main tutorial notebook
├── agentcore/                  # Agent application
│   ├── app.py                 # Main agent entry point
│   ├── create_booking.py      # Booking creation tool
│   ├── delete_booking.py      # Booking deletion tool
│   ├── get_booking.py         # Booking retrieval tool
│   ├── Dockerfile             # Container configuration
│   └── requirements.txt       # Python dependencies
├── prereqs/                   # Infrastructure setup
│   ├── dynamodb.py           # DynamoDB table creation
│   ├── knowledge_base.py     # Knowledge Base setup
│   └── kb_files/             # Restaurant data files
├── deploy_prereqs.sh         # Infrastructure deployment script
├── cleanup.sh                # Resource cleanup script
├── agent-requirements.txt    # Notebook dependencies
└── README.md                 # This file
```

## Agent Capabilities

The restaurant booking agent can:

- **Restaurant Discovery**: Browse available restaurants
- **Menu Information**: Get detailed menu and pricing information
- **Reservation Management**: Create, view, and cancel bookings
- **Natural Conversation**: Handle complex, multi-turn conversations
- **Data Validation**: Ensure booking information is complete and valid

## Key Features

### Serverless Scaling
- Automatically scales from zero to handle any traffic volume
- Pay only for actual usage with no idle costs
- Built-in load balancing and fault tolerance

### Session Management
- Each conversation is securely isolated
- Automatic session state management
- No manual session handling required

### Enterprise Integration
- Native AWS service integration
- VPC networking support for enhanced security
- IAM-based access controls
- Comprehensive CloudWatch monitoring

### Container-Based Deployment
- Consistent environment across development and production
- Easy dependency management
- Version control and rollback capabilities
- Built-in security scanning

## Configuration

The agent is configured through environment variables and AWS services:

- **AWS_REGION**: Target AWS region (default: us-east-1)
- **Knowledge Base**: Restaurant information and menus
- **DynamoDB Table**: Booking data storage
- **Parameter Store**: Configuration parameters

## Monitoring and Observability

The deployment includes comprehensive monitoring:

- **CloudWatch Logs**: Application logs and errors
- **CloudWatch Metrics**: Performance and usage metrics
- **X-Ray Tracing**: Request tracing with OpenTelemetry
- **Health Checks**: Automatic health monitoring

## Security

Security is implemented at multiple layers:

- **IAM Roles**: Least-privilege access controls
- **VPC Networking**: Network isolation (configurable)
- **Container Security**: Non-root user execution
- **Encryption**: Data encryption at rest and in transit

## Cost Optimization

- **Serverless Architecture**: No idle costs
- **Efficient Resource Usage**: Optimized container images
- **Automatic Scaling**: Scale to zero when not in use
- **Shared Infrastructure**: Leverage managed AWS services

## Troubleshooting

### Common Issues

1. **Runtime Creation Fails**
   - Check IAM permissions
   - Verify container image is pushed to ECR
   - Ensure AgentCore quota limits

2. **Agent Invocation Errors**
   - Check CloudWatch logs for detailed errors
   - Verify IAM role has required permissions
   - Ensure all AWS services are properly configured

3. **Container Build Issues**
   - Verify Docker daemon is running
   - Check ECR authentication
   - Review Dockerfile for syntax errors

### Debug Resources

- CloudWatch Logs: `/aws/bedrock-agentcore/runtimes/{runtime-id}`
- AWS Console: AgentCore Runtime status and configuration
- ECR Console: Container image status and scanning results

## Support

For issues and questions:

- [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/)
- [Strands Framework Documentation](https://github.com/AustinMLJourneys/strands)
- AWS Support (for enterprise customers)

## License

This tutorial is provided under the MIT License. See the main repository for full license details.