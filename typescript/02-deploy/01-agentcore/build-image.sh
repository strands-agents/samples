#!/bin/bash
# Build and push Docker image to ECR
# Supports local Docker or AWS CodeBuild (for environments like SageMaker Studio)
set -e

AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPO_NAME="${ECR_REPO_NAME:-agentcore-deployment}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REPO_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME"

# Check if Docker is available
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "Building with local Docker..."

    aws ecr get-login-password --region $AWS_REGION | \
        docker login --username AWS --password-stdin ${REPO_URI%%/*}

    docker buildx build --platform linux/arm64 -t $REPO_URI:latest --push .

    echo "Image pushed to: $REPO_URI:latest"
else
    echo "Docker not available. Building with AWS CodeBuild..."

    # Create buildspec inline
    BUILDSPEC=$(cat <<'BUILDSPEC_EOF'
version: 0.2
phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $ECR_REPO_URI
  build:
    commands:
      - echo Building Docker image...
      - docker build --platform linux/arm64 -t $ECR_REPO_URI:latest .
  post_build:
    commands:
      - echo Pushing Docker image...
      - docker push $ECR_REPO_URI:latest
      - echo Build completed on `date`
BUILDSPEC_EOF
)

    # Create CodeBuild project if it doesn't exist
    PROJECT_NAME="agentcore-image-builder"

    if ! aws codebuild batch-get-projects --names $PROJECT_NAME --query 'projects[0].name' --output text 2>/dev/null | grep -q $PROJECT_NAME; then
        echo "Creating CodeBuild project..."

        # Create service role for CodeBuild
        CODEBUILD_ROLE_NAME="CodeBuildAgentCoreRole"

        if ! aws iam get-role --role-name $CODEBUILD_ROLE_NAME 2>/dev/null; then
            aws iam create-role \
                --role-name $CODEBUILD_ROLE_NAME \
                --assume-role-policy-document '{
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Principal": {"Service": "codebuild.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }]
                }'

            aws iam put-role-policy \
                --role-name $CODEBUILD_ROLE_NAME \
                --policy-name CodeBuildPolicy \
                --policy-document '{
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents"
                            ],
                            "Resource": "*"
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "ecr:GetAuthorizationToken",
                                "ecr:BatchCheckLayerAvailability",
                                "ecr:GetDownloadUrlForLayer",
                                "ecr:BatchGetImage",
                                "ecr:PutImage",
                                "ecr:InitiateLayerUpload",
                                "ecr:UploadLayerPart",
                                "ecr:CompleteLayerUpload"
                            ],
                            "Resource": "*"
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "s3:GetObject",
                                "s3:PutObject"
                            ],
                            "Resource": "*"
                        }
                    ]
                }'

            echo "Waiting for IAM role propagation..."
            sleep 10
        fi

        CODEBUILD_ROLE_ARN="arn:aws:iam::$AWS_ACCOUNT_ID:role/$CODEBUILD_ROLE_NAME"

        aws codebuild create-project \
            --name $PROJECT_NAME \
            --source type=NO_SOURCE,buildspec="$BUILDSPEC" \
            --artifacts type=NO_ARTIFACTS \
            --environment type=ARM_CONTAINER,computeType=BUILD_GENERAL1_SMALL,image=aws/codebuild/amazonlinux2-aarch64-standard:3.0,privilegedMode=true \
            --service-role $CODEBUILD_ROLE_ARN \
            --region $AWS_REGION
    fi

    # Create S3 bucket for source code
    BUCKET_NAME="codebuild-source-$AWS_ACCOUNT_ID-$AWS_REGION"
    if ! aws s3 ls "s3://$BUCKET_NAME" 2>/dev/null; then
        aws s3 mb "s3://$BUCKET_NAME" --region $AWS_REGION
    fi

    # Package and upload source
    echo "Packaging source code..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    (cd "$SCRIPT_DIR" && zip -r /tmp/source.zip . -x "*.git*" -x "node_modules/*")
    aws s3 cp /tmp/source.zip "s3://$BUCKET_NAME/agentcore-source.zip"

    # Start build
    echo "Starting CodeBuild..."
    BUILD_ID=$(aws codebuild start-build \
        --project-name $PROJECT_NAME \
        --source-type-override S3 \
        --source-location-override "$BUCKET_NAME/agentcore-source.zip" \
        --environment-variables-override \
            name=ECR_REPO_URI,value=$REPO_URI \
            name=AWS_DEFAULT_REGION,value=$AWS_REGION \
        --query 'build.id' --output text)

    echo "Build started: $BUILD_ID"
    echo "Waiting for build to complete..."

    # Wait for build
    while true; do
        STATUS=$(aws codebuild batch-get-builds --ids $BUILD_ID --query 'builds[0].buildStatus' --output text)
        if [ "$STATUS" = "SUCCEEDED" ]; then
            echo "Build succeeded!"
            break
        elif [ "$STATUS" = "FAILED" ] || [ "$STATUS" = "FAULT" ] || [ "$STATUS" = "STOPPED" ]; then
            echo "Build failed with status: $STATUS"
            echo "Check CloudWatch logs for details"
            exit 1
        fi
        echo "  Status: $STATUS..."
        sleep 15
    done

    echo "Image pushed to: $REPO_URI:latest"
fi

echo ""
echo "Export for deployment:"
echo "  export REPO_URI=$REPO_URI"
