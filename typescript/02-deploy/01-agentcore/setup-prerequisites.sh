#!/bin/bash
# Setup script for Amazon Bedrock AgentCore Runtime prerequisites
# Creates IAM role and ECR repository
set -e

# Configuration
ECR_REPO_NAME="${ECR_REPO_NAME:-agentcore-deployment}"
ROLE_NAME="${ROLE_NAME:-AgentCoreRuntimeRole}"
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Setting up AgentCore prerequisites..."
echo "  Region: $AWS_REGION"
echo "  Account: $AWS_ACCOUNT_ID"
echo "  Role: $ROLE_NAME"
echo "  ECR Repo: $ECR_REPO_NAME"
echo ""

# Create IAM Role
echo "Creating IAM role..."

TRUST_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock-agentcore.amazonaws.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "$AWS_ACCOUNT_ID"
        },
        "ArnLike": {
          "aws:SourceArn": "arn:aws:bedrock-agentcore:$AWS_REGION:$AWS_ACCOUNT_ID:*"
        }
      }
    }
  ]
}
EOF
)

PERMISSIONS_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ECRImageAccess",
      "Effect": "Allow",
      "Action": [
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer"
      ],
      "Resource": "arn:aws:ecr:$AWS_REGION:$AWS_ACCOUNT_ID:repository/*"
    },
    {
      "Sid": "ECRTokenAccess",
      "Effect": "Allow",
      "Action": "ecr:GetAuthorizationToken",
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchLogsAccess",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Resource": [
        "arn:aws:logs:$AWS_REGION:$AWS_ACCOUNT_ID:log-group:/aws/bedrock-agentcore/runtimes/*",
        "arn:aws:logs:$AWS_REGION:$AWS_ACCOUNT_ID:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*"
      ]
    },
    {
      "Sid": "XRayAccess",
      "Effect": "Allow",
      "Action": [
        "xray:PutTraceSegments",
        "xray:PutTelemetryRecords",
        "xray:GetSamplingRules",
        "xray:GetSamplingTargets"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchMetrics",
      "Effect": "Allow",
      "Action": "cloudwatch:PutMetricData",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "cloudwatch:namespace": "bedrock-agentcore"
        }
      }
    },
    {
      "Sid": "BedrockModelInvocation",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/*",
        "arn:aws:bedrock:$AWS_REGION:$AWS_ACCOUNT_ID:*"
      ]
    }
  ]
}
EOF
)

# Check if role exists
if aws iam get-role --role-name "$ROLE_NAME" 2>/dev/null; then
  echo "  Role '$ROLE_NAME' already exists"
else
  aws iam create-role \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document "$TRUST_POLICY" \
    --description "Execution role for AgentCore Runtime" \
    --output text --query 'Role.Arn'

  aws iam put-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-name "AgentCoreRuntimePolicy" \
    --policy-document "$PERMISSIONS_POLICY"

  echo "  Role created successfully"
fi

ROLE_ARN="arn:aws:iam::$AWS_ACCOUNT_ID:role/$ROLE_NAME"

# Create ECR Repository
echo "Creating ECR repository..."

if aws ecr describe-repositories --repository-names "$ECR_REPO_NAME" --region "$AWS_REGION" 2>/dev/null; then
  echo "  Repository '$ECR_REPO_NAME' already exists"
else
  aws ecr create-repository \
    --repository-name "$ECR_REPO_NAME" \
    --region "$AWS_REGION" \
    --image-scanning-configuration scanOnPush=true \
    --output text --query 'repository.repositoryUri'

  # Add lifecycle policy to keep only last 5 images
  aws ecr put-lifecycle-policy \
    --repository-name "$ECR_REPO_NAME" \
    --region "$AWS_REGION" \
    --lifecycle-policy-text '{
      "rules": [{
        "rulePriority": 1,
        "description": "Keep last 5 images",
        "selection": {
          "tagStatus": "any",
          "countType": "imageCountMoreThan",
          "countNumber": 5
        },
        "action": {"type": "expire"}
      }]
    }'

  echo "  Repository created successfully"
fi

REPO_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME"

echo ""
echo "Setup complete!"
echo ""
echo "Export these variables for deployment:"
echo "  export ROLE_ARN=$ROLE_ARN"
echo "  export REPO_URI=$REPO_URI"
echo "  export AWS_REGION=$AWS_REGION"
