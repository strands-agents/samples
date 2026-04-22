#!/usr/bin/env bash

set -euo pipefail

source .slack_secrets

uv run app.py
