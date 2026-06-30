#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-slack-assistant}"
REGION="${AWS_REGION:-us-west-2}"
TAG="${TAG:-latest}"
STACK_NAME="${STACK_NAME:-slack-assistant}"

ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
URI="$ACCOUNT.dkr.ecr.$REGION.amazonaws.com/$REPO:$TAG"

if aws ecr describe-repositories --repository-names "$REPO" --region "$REGION" >/dev/null 2>&1; then
  echo "ECR repo $REPO exists"
else
  echo "Creating ECR repo $REPO"
  aws ecr create-repository --repository-name "$REPO" --region "$REGION" >/dev/null
fi

aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "$ACCOUNT.dkr.ecr.$REGION.amazonaws.com"

docker build --platform linux/amd64,linux/arm64 -t "$URI" --push .

source .slack_secrets

aws cloudformation deploy \
  --stack-name "$STACK_NAME" \
  --template-file infra.yaml \
  --region "$REGION" \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    Image="$URI" \
    SlackBotToken="$SLACK_BOT_TOKEN" \
    SlackSigningSecret="$SLACK_SIGNING_SECRET"

aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs" \
  --output table

