#!/usr/bin/env bash
# Copyright 2026 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Destroy the Order Approval Agent infrastructure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Destroying OrderApprovalAgent stack..."
uv run cdk destroy --force

echo "Removing cdk-outputs.json..."
rm -f "$SCRIPT_DIR/cdk-outputs.json"

echo "Removing .env files..."
rm -f "$SCRIPT_DIR/../src/.env"
rm -f "$SCRIPT_DIR/../streamlit_app/.env"

echo "Cleanup complete."
