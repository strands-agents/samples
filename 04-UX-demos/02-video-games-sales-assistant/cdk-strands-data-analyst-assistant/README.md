# Generative AI Application - Data Source and Strands Agent Deployment with CDK

This tutorial guides you through setting up the back-end infrastructure and agent for a Data Analyst Assistant for Video Game Sales using **[AWS Cloud Development Kit (CDK)](https://aws.amazon.com/cdk/)**.

## Overview

You will deploy the following AWS services:

- **Strands Agents SDK**: Powers the ***Data Analyst Assistant*** that answers questions by generating SQL queries using Claude 3.7 Sonnet
    - Strands Agents is a simple yet powerful SDK that takes a model-driven approach to building and running AI agents. From simple conversational assistants to complex autonomous workflows, from local development to production deployment, Strands Agents scales with your needs.
- **Amazon Aurora PostgreSQL**: Stores the video game sales data
- **Amazon ECS on Fargate**: Hosts the Strands Agent service
- **Application Load Balancer**: Acts as the entry point to your agent
- **Amazon S3**: Provides a bucket for importing data into Aurora
- **AWS Secrets Manager**: Securely stores database credentials
- **AWS Systems Manager Parameter Store**: Stores configuration parameters for the application (database ARNs, table names, and other runtime settings)
- **RDS Proxy**: Manages database connections efficiently
- **Amazon VPC**: Provides network isolation for the database

By completing this tutorial, you'll have a fully functional data analyst assistant accessible via an API endpoint.

> [!IMPORTANT]
> This sample application is meant for demo purposes and is not production ready. Please make sure to validate the code with your organizations security best practices.
>
> Remember to clean up resources after testing to avoid unnecessary costs by following the clean-up steps provided.

## Prerequisites

Before you begin, ensure you have:

* **[AWS CDK Installed](https://docs.aws.amazon.com/cdk/v2/guide/getting-started.html)**
* **[Docker](https://www.docker.com)**
* Anthropic Claude 3.7 Sonnet model enabled in Amazon Bedrock
* Run this command to create a service-linked role for RDS:

```bash
aws iam create-service-linked-role --aws-service-name rds.amazonaws.com
```

* Authenticate with Amazon ECR Public registry to pull required container images:

```bash
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws
```

## Deploy the Back-End Services with AWS CDK

Navigate to the CDK project folder (cdk-strands-data-analyst-assistant) and install the required npm dependencies::

``` bash
npm install
```

Deploy the infrastructure stack to AWS:

``` bash
cdk deploy
```

It will use the following default value parameters:

- **ProjectId**: "strands-data-analyst-assistant" - Project identifier used for naming resources in SSM Paramters
- **DatabaseName**: "video_games_sales" - Database name for video games sales data
- **MaxResponseSize**: 25600 - Maximum size for row query results in bytes
- **TaskCpu**: 2048 - CPU units for Fargate task (256=0.25vCPU, 512=0.5vCPU, 1024=1vCPU, 2048=2vCPU, 4096=4vCPU)
- **TaskMemory**: 4096 - Memory (in MiB) for Fargate task
- **ServiceDesiredCount**: 1 - Desired count of tasks for the Fargate service
- **LastNumberOfMessages**: 20 - Number of last messages to retrieve from chat history
- **WebApplicationUrl**: "http://localhost:3000" - URL of the web application frontend for local testing
- **CognitoUserPoolId**: "N/A" - Cognito User Pool ID for frontend authentication

After deployment completes, the following resources will be created:

- **Strands Agent Service**: Deployed on AWS Fargate with an Application Load Balancer, making it accessible via a simple HTTP API endpoint
- **Amazon Aurora PostgreSQL Cluster**: Serverless v2 cluster for storing video game sales data with Data API enabled
- **Amazon VPC**: Custom VPC with public and private subnets, NAT Gateway, and VPC endpoints for S3 and DynamoDB
- **Amazon S3 Bucket**: For importing data into Aurora using the aws_s3 extension
- **AWS Secrets Manager**: Secret for securely storing database credentials
- **AWS Systems Manager Parameter Store**: Configuration parameters for database ARNs, table names, and application settings
- **Amazon DynamoDB Tables**: Two tables for storing query results and conversation history
- **Amazon ECS Cluster**: Fargate cluster with container insights for running the agent service
- **Application Load Balancer**: Internet-facing ALB with target group and health checks

> [!IMPORTANT] 
> Enhance AI safety and compliance by implementing **[Amazon Bedrock Guardrails](https://aws.amazon.com/bedrock/guardrails/)** for your AI applications with the seamless integration offered by **[Strands Agents SDK](https://strandsagents.com/latest/user-guide/safety-security/guardrails/)**.

## Load Sample Data into PostgreSQL Database

Set up the required environment variables:

``` bash
# Set the stack name environment variable
export STACK_NAME=CdkStrandsDataAnalystAssistantStack

# Retrieve the stack input parameters
export PROJECT_ID=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Parameters[?ParameterKey=='ProjectId'].ParameterValue" --output text)
export WEB_APPLICATION_URL=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Parameters[?ParameterKey=='WebApplicationUrl'].ParameterValue" --output text)

# Retrieve the output values and store them in environment variables
export SECRET_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='SecretARN'].OutputValue" --output text)
export DATA_SOURCE_BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='DataSourceBucketName'].OutputValue" --output text)
export AURORA_SERVERLESS_DB_CLUSTER_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='AuroraServerlessDBClusterARN'].OutputValue" --output text)
export AGENT_ENDPOINT_URL=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='AgentEndpointURL'].OutputValue" --output text)
cat << EOF
STACK_NAME: ${STACK_NAME}
PROJECT_ID: ${PROJECT_ID}
WEB_APPLICATION_URL: ${WEB_APPLICATION_URL}
SECRET_ARN: ${SECRET_ARN}
DATA_SOURCE_BUCKET_NAME: ${DATA_SOURCE_BUCKET_NAME}
AURORA_SERVERLESS_DB_CLUSTER_ARN: ${AURORA_SERVERLESS_DB_CLUSTER_ARN}
AGENT_ENDPOINT_URL: ${AGENT_ENDPOINT_URL}
EOF

```

Execute the following command to create the database and load the sample data:

``` bash
python3 resources/create-sales-database.py
```

The script uses the **[video_games_sales_no_headers.csv](./resources/database/video_games_sales_no_headers.csv)** as the data source.

> [!NOTE]
> The data source provided contains information from [Video Game Sales](https://www.kaggle.com/datasets/asaniczka/video-game-sales-2024) which is made available under the [ODC Attribution License](https://opendatacommons.org/licenses/odbl/1-0/).

## Testing the Deployed Agent

### Default Configuration (No Authentication Required)

By default, the stack deploys with Cognito authentication **disabled** (COGNITO_USER_POOL_ID parameter set to "N/A"). This configuration is designed for **development and testing purposes** and provides the following behavior:

- **No JWT token validation** - The Authorization header is still required in API requests for consistency, but the actual token value is not validated against any identity provider
- **Open access** - Any client can make requests to the agent endpoint without proper authentication
- **Session tracking enabled** - Each request can include a `session_id` parameter for conversation continuity across multiple interactions
- **Conversation memory** - The agent maintains context and remembers previous questions within the same session, stored in DynamoDB

> [!WARNING]
> **Security Notice**: This default configuration bypasses authentication and should **NOT be used in production environments**. For production deployments, configure a valid Cognito User Pool ID to enable proper JWT token validation and user authentication. The Cognito setup and configuration process is covered in detail in the **[Front-End Implementation tutorial](../amplify-video-games-sales-assistant-strands/)**.

### Setting Up Test Environment

Since Cognito is not configured, you can use a placeholder token (it won't be validated) and generate a session ID for testing:

```bash
# Set a placeholder JWT token (not validated when Cognito is disabled)
export JWT_TOKEN="no-token-required"
```

Create a session ID for conversation tracking:

```bash
export SESSION_ID=$(uuidgen)
```

### Example Queries

Test the agent with these sample queries. Each request includes the session ID for conversation continuity:

```bash
curl -d '{ "prompt": "Hello!", "session_id": "'$SESSION_ID'" }' -X POST -H 'Content-Type: application/json' -H "Authorization: Bearer $JWT_TOKEN" http://$AGENT_ENDPOINT_URL/assistant-streaming
```

```bash
curl -d '{ "prompt": "How can you help me?", "session_id": "'$SESSION_ID'" }' -X POST -H 'Content-Type: application/json' -H "Authorization: Bearer $JWT_TOKEN" http://$AGENT_ENDPOINT_URL/assistant-streaming
```

```bash
curl -d '{ "prompt": "What is the structure of the data?", "session_id": "'$SESSION_ID'" }' -X POST -H 'Content-Type: application/json' -H "Authorization: Bearer $JWT_TOKEN" http://$AGENT_ENDPOINT_URL/assistant-streaming
```

```bash
curl -d '{ "prompt": "Which developers tend to get the best reviews?", "session_id": "'$SESSION_ID'" }' -X POST -H 'Content-Type: application/json' -H "Authorization: Bearer $JWT_TOKEN" http://$AGENT_ENDPOINT_URL/assistant-streaming
```

```bash
curl -d '{ "prompt": "What were the total sales for each region between 2000 and 2010? Give me the data in percentages.", "session_id": "'$SESSION_ID'" }' -X POST -H 'Content-Type: application/json' -H "Authorization: Bearer $JWT_TOKEN" http://$AGENT_ENDPOINT_URL/assistant-streaming
```

```bash
curl -d '{ "prompt": "What were the best-selling games in the last 10 years?", "session_id": "'$SESSION_ID'" }' -X POST -H 'Content-Type: application/json' -H "Authorization: Bearer $JWT_TOKEN" http://$AGENT_ENDPOINT_URL/assistant-streaming
```

```bash
curl -d '{ "prompt": "What are the best-selling video game genres?", "session_id": "'$SESSION_ID'" }' -X POST -H 'Content-Type: application/json' -H "Authorization: Bearer $JWT_TOKEN" http://$AGENT_ENDPOINT_URL/assistant-streaming
```

```bash
curl -d '{ "prompt": "Give me the top 3 game publishers.", "session_id": "'$SESSION_ID'" }' -X POST -H 'Content-Type: application/json' -H "Authorization: Bearer $JWT_TOKEN" http://$AGENT_ENDPOINT_URL/assistant-streaming
```

```bash
curl -d '{ "prompt": "Give me the top 3 video games with the best reviews and the best sales.", "session_id": "'$SESSION_ID'" }' -X POST -H 'Content-Type: application/json' -H "Authorization: Bearer $JWT_TOKEN" http://$AGENT_ENDPOINT_URL/assistant-streaming
```

```bash
curl -d '{ "prompt": "Which is the year with the highest number of games released?", "session_id": "'$SESSION_ID'" }' -X POST -H 'Content-Type: application/json' -H "Authorization: Bearer $JWT_TOKEN" http://$AGENT_ENDPOINT_URL/assistant-streaming
```

```bash
curl -d '{ "prompt": "Which are the most popular consoles and why?", "session_id": "'$SESSION_ID'" }' -X POST -H 'Content-Type: application/json' -H "Authorization: Bearer $JWT_TOKEN" http://$AGENT_ENDPOINT_URL/assistant-streaming
```

```bash
curl -d '{ "prompt": "Give me a short summary and conclusion of our conversation.", "session_id": "'$SESSION_ID'" }' -X POST -H 'Content-Type: application/json' -H "Authorization: Bearer $JWT_TOKEN" http://$AGENT_ENDPOINT_URL/assistant-streaming
```

### Expected Behavior

The agent responds as "Gus," a video game sales data analyst assistant who:

- **Provides data insights** from the video_games_sales_units database (64,016 game titles from 1971-2024)
- **Analyzes developer review scores** and sales performance
- **Session Continuity**: Use the same `SESSION_ID` for all related questions to maintain conversation context
- **Authentication Bypass**: When COGNITO_USER_POOL_ID is set to "N/A", the Authorization header is still required but the JWT token is not validated

> **Note**: The system still expects the `Authorization: Bearer <token>` header in all requests, but when Cognito is not configured (COGNITO_USER_POOL_ID="N/A"), any token value will be accepted without validation.

You can now proceed to the **[Front-End Implementation - Integrating Strands Agent with a Ready-to-Use Data Analyst Assistant Application](../amplify-video-games-sales-assistant-strands/)**.

## Cleaning-up Resources (Optional)

To avoid unnecessary charges, delete the CDK stack:

``` bash
cdk destroy
```

## Thank You

## License

This project is licensed under the Apache-2.0 License.