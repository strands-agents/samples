#!/usr/bin/env bash
# Copyright 2026 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Deploy the Order Approval Agent infrastructure using AWS CDK.
# Outputs the ARNs and resource names needed to configure the Streamlit app.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Installing CDK dependencies..."
uv sync

echo "Bootstrapping CDK (first time only)..."
uv run cdk bootstrap || true

echo "Deploying OrderApprovalAgent stack..."
uv run cdk deploy --require-approval never --outputs-file cdk-outputs.json

echo ""
echo "Deployment complete. Stack outputs saved to cdk-outputs.json"
echo "Copy the values into your .env file:"
echo ""
cat cdk-outputs.json
