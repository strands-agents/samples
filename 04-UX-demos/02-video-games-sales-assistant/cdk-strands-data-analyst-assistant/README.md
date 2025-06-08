# Generative AI Application - Data Source and Strands Agent Deployment with CDK

This tutorial guides you through setting up the back-end infrastructure and agent for a Data Analyst Assistant for Video Game Sales using AWS Cloud Development Kit (CDK).

## Overview

You will deploy the following AWS services:

- **Strands Agents SDK**: Powers the ***Data Analyst Assistant*** that answers questions by generating SQL queries using Claude 3.7 Sonnet
    - Strands Agents is a simple yet powerful SDK that takes a model-driven approach to building and running AI agents. From simple conversational assistants to complex autonomous workflows, from local development to production deployment, Strands Agents scales with your needs.
- **Amazon Aurora PostgreSQL**: Stores the video game sales data
- **Amazon ECS on Fargate**: Hosts the Strands Agent service
- **Application Load Balancer**: Acts as the entry point to your agent
- **Amazon S3**: Provides a bucket for importing data into Aurora
- **AWS Secrets Manager**: Securely stores database credentials
- **RDS Proxy**: Manages database connections efficiently
- **Amazon VPC**: Provides network isolation for the database

By completing this tutorial, you'll have a fully functional data analyst assistant accessible via an API endpoint.

> [!IMPORTANT]
> This sample application is meant for demo purposes and is not production ready. Please make sure to validate the code with your organizations security best practices.
>
> Remember to clean up resources after testing to avoid unnecessary costs by following the clean-up steps provided.

## Prerequisites

Before you begin, ensure you have:

* [AWS CDK Installed](https://docs.aws.amazon.com/cdk/v2/guide/getting-started.html)
* [Docker](https://www.docker.com)
* Anthropic Claude 3.7 Sonnet model enabled in Amazon Bedrock
* Run this command to create a service-linked role for RDS:

```bash
aws iam create-service-linked-role --aws-service-name rds.amazonaws.com
```

## Deploy the Back-End Services with AWS CDK

Navigate to the CDK project folder and execute:

```bash
cdk deploy
```

It will use the following default value parameters:

- **ProjectId**: "strands-data-analyst-assistant" - Project identifier used for naming resources
- **DatabaseName**: "video_games_sales" - Nombre de la base de datos
- **MaxResponseSize**: 25600 - Maximum size for row query results in bytes
- **TaskCpu**: 2048 - CPU units for Fargate task (256=0.25vCPU, 512=0.5vCPU, 1024=1vCPU, 2048=2vCPU, 4096=4vCPU)
- **TaskMemory**: 4096 - Memory (in MiB) for Fargate task
- **ServiceDesiredCount**: 1 - Desired count of tasks for the Fargate service

After deployment completes, the following resources will be created:

- Strands Agent deployed on AWS Fargate with an Application Load Balancer, making it accessible via a simple HTTP API endpoint
- Aurora PostgreSQL Cluster with RDS Proxy
- S3 bucket for data import
- Secrets Manager secret for database credentials

## Load Sample Data into PostgreSQL Database

Set up the required environment variables:

``` bash
# Set the stack name environment variable
export STACK_NAME=CdkStrandsDataAnalystAssistantStack

# Retrieve the output values and store them in environment variables
export SECRET_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='SecretARN'].OutputValue" --output text)
export DATA_SOURCE_BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='DataSourceBucketName'].OutputValue" --output text)
export AURORA_SERVERLESS_DB_CLUSTER_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='AuroraServerlessDBClusterARN'].OutputValue" --output text)
export AGENT_ENDPOINT_URL=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='AgentEndpointURL'].OutputValue" --output text)
cat << EOF
STACK_NAME: ${STACK_NAME}
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

## Test the Agent

You can test your agent using the HTTP client such as curl or Postman:

```bash
curl -X POST http://$AGENT_ENDPOINT_URL/assistant-streaming -H 'Content-Type: application/json' -d '{ "prompt": "Hello!" }'
```

Try these sample questions:

- Hello!
- How can you help me?
- What is the structure of the data?
- Which developers tend to get the best reviews?
- What were the total sales for each region between 2000 and 2010? Give me the data in percentages.
- What were the best-selling games in the last 10 years?
- What are the best-selling video game genres?
- Give me the top 3 game publishers.
- Give me the top 3 video games with the best reviews and the best sales.
- Which is the year with the highest number of games released?
- Which are the most popular consoles and why?
- Give me a short summary and conclusion of our conversation.

You can now proceed to the [Front-End Implementation - Integrating Strands Agent with a Ready-to-Use Data Analyst Assistant Application](../amplify-video-games-sales-assistant-strands/).

## Cleaning-up Resources (Optional)

To avoid unnecessary charges, delete the CDK stack:

``` bash
cdk destroy
```

## Thank You

## License

This project is licensed under the Apache-2.0 License.