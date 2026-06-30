#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-slack-assistant}"
REGION="${AWS_REGION:-us-west-2}"
STACK_NAME="${STACK_NAME:-slack-assistant}"

echo "Deleting CloudFormation stack $STACK_NAME in $REGION..."
aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$REGION"

echo "Waiting for stack deletion to complete..."
aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$REGION"
echo "Stack $STACK_NAME deleted."

echo "Deleting ECR repository $REPO in $REGION..."
aws ecr delete-repository --repository-name "$REPO" --region "$REGION" --force
echo "ECR repository $REPO deleted."
