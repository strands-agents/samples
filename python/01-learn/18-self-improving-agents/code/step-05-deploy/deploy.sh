#!/usr/bin/env bash
# Configure + deploy the agent to Amazon Bedrock AgentCore Runtime
# using the new @aws/agentcore CLI (github.com/aws/agentcore-cli).
#
# This script wraps `agentcore create` + `agentcore add agent --type byo`
# + `agentcore deploy` into a single idempotent workflow.
#
# Run from code/step-05-deploy/
set -euo pipefail

PROJECT_NAME="${AIM308_PROJECT_NAME:-Aim308Deploy}"
AGENT_NAME="${AIM308_AGENT_NAME:-aim308_research_agent}"
REGION="${AWS_REGION:-us-east-1}"
PROJECT_DIR="${AIM308_PROJECT_DIR:-./$PROJECT_NAME}"

# --- preflight checks -------------------------------------------------------

if ! command -v agentcore >/dev/null; then
    echo "⚠️  'agentcore' CLI not found."
    echo ""
    echo "Install the new AgentCore CLI (Node 20+ required):"
    echo "    npm install -g @aws/agentcore"
    echo ""
    echo "If Node 20 isn't available, install via nvm:"
    echo "    nvm install 20 && nvm use 20"
    exit 1
fi

# Validate we have Node 20+
NODE_MAJOR=$(node -v | sed 's/v//' | cut -d. -f1)
if [[ "$NODE_MAJOR" -lt 20 ]]; then
    echo "⚠️  Node.js $NODE_MAJOR detected — @aws/agentcore needs Node 20+."
    echo "    nvm install 20 && nvm use 20"
    exit 1
fi

if [[ -z "${BEDROCK_AGENTCORE_MEMORY_ID:-}" ]]; then
    echo "⚠️  export BEDROCK_AGENTCORE_MEMORY_ID=<id> first"
    echo "   (run ../step-03-memory/create_memory.py if needed)"
    exit 1
fi

CODE_LOCATION="$(cd "$(dirname "$0")" && pwd)"

# --- step 1: create the AgentCore project (if not already there) -----------

if [[ ! -d "$PROJECT_DIR" ]]; then
    echo "🏗️  Creating AgentCore project: $PROJECT_NAME"
    agentcore create \
        --name "$PROJECT_NAME" \
        --no-agent \
        --defaults \
        --skip-install \
        --skip-python-setup \
        --skip-git
else
    echo "📦 Reusing existing project: $PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# --- step 2: register our agent.py as a BYO agent --------------------------

if ! grep -q "\"name\": \"$AGENT_NAME\"" agentcore/agentcore.json; then
    echo "🔗 Registering agent '$AGENT_NAME' (BYO from $CODE_LOCATION)"
    agentcore add agent \
        --name "$AGENT_NAME" \
        --type byo \
        --language Python \
        --framework Strands \
        --model-provider Bedrock \
        --code-location "$CODE_LOCATION" \
        --entrypoint agent.py \
        --protocol HTTP
else
    echo "✓ Agent '$AGENT_NAME' already registered"
fi

# --- step 3: inject runtime env vars into .env.local ----------------------

ENV_FILE="agentcore/.env.local"
touch "$ENV_FILE"
grep -q "^AWS_REGION=" "$ENV_FILE"                 || echo "AWS_REGION=$REGION" >> "$ENV_FILE"
grep -q "^BEDROCK_AGENTCORE_MEMORY_ID=" "$ENV_FILE" || \
    echo "BEDROCK_AGENTCORE_MEMORY_ID=$BEDROCK_AGENTCORE_MEMORY_ID" >> "$ENV_FILE"

# --- step 4: install deps & deploy via CDK --------------------------------

echo "📦 Installing CDK deps..."
(cd agentcore/cdk && npm install --no-audit --no-fund --loglevel=error)

echo "🚀 Deploying via CDK..."
agentcore deploy -y

echo ""
echo "✅ Done!"
echo ""
echo "Invoke:   (cd $PROJECT_DIR && agentcore invoke 'hello, who are you?')"
echo "Status:   (cd $PROJECT_DIR && agentcore status)"
echo "Logs:     (cd $PROJECT_DIR && agentcore logs)"
