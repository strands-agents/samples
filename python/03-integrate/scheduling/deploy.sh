#!/usr/bin/env bash
set -euo pipefail

# ── Configuration ──────────────────────────────────────────────
STACK_NAME="${STACK_NAME:-scheduled-agentcore}"
AGENT_NAME="${AGENT_NAME:-scheduled_agentcore_agent}"
REGION="${AWS_REGION:-us-east-1}"
SCHEDULE_EXPR="${SCHEDULE_EXPR:-rate(1 hour)}"
SCHEDULE_PAYLOAD="${SCHEDULE_PAYLOAD:-{\"prompt\":\"You are triggered by a schedule. Report the current time and confirm you are running.\"}}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="${STACK_NAME}-agent"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPO}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "══════════════════════════════════════════════════════════"
echo "  Account:   ${ACCOUNT_ID}"
echo "  Region:    ${REGION}"
echo "  Stack:     ${STACK_NAME}"
echo "  Schedule:  ${SCHEDULE_EXPR}"
echo "══════════════════════════════════════════════════════════"

# ── Step 1: ECR ────────────────────────────────────────────────
echo -e "\n▶ Step 1/5: ECR repository..."
aws ecr describe-repositories --repository-names "${ECR_REPO}" --region "${REGION}" >/dev/null 2>&1 \
  || aws ecr create-repository --repository-name "${ECR_REPO}" --region "${REGION}" --output text >/dev/null

aws ecr get-login-password --region "${REGION}" \
  | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com" 2>/dev/null

# ── Step 2: Build & push container ─────────────────────────────
echo -e "\n▶ Step 2/5: Building agent container (ARM64)..."
docker buildx build --platform linux/arm64 \
  -t "${ECR_URI}:latest" --push "${SCRIPT_DIR}/agent"

# ── Step 3: AgentCore execution role ───────────────────────────
echo -e "\n▶ Step 3/5: AgentCore execution role..."
ROLE_NAME="${STACK_NAME}-AgentCoreRole"

ROLE_ARN=$(aws iam get-role --role-name "${ROLE_NAME}" --query 'Role.Arn' --output text 2>/dev/null || echo "")
if [ -z "${ROLE_ARN}" ] || [ "${ROLE_ARN}" = "None" ]; then
  ROLE_ARN=$(aws iam create-role \
    --role-name "${ROLE_NAME}" \
    --assume-role-policy-document "{
      \"Version\":\"2012-10-17\",
      \"Statement\":[{
        \"Effect\":\"Allow\",
        \"Principal\":{\"Service\":\"bedrock-agentcore.amazonaws.com\"},
        \"Action\":\"sts:AssumeRole\",
        \"Condition\":{
          \"StringEquals\":{\"aws:SourceAccount\":\"${ACCOUNT_ID}\"},
          \"ArnLike\":{\"aws:SourceArn\":\"arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:*\"}
        }
      }]
    }" --query 'Role.Arn' --output text)
  echo "  Created: ${ROLE_ARN}"
else
  echo "  Exists: ${ROLE_ARN}"
fi

aws iam put-role-policy --role-name "${ROLE_NAME}" \
  --policy-name AgentCorePolicy \
  --policy-document "{
    \"Version\":\"2012-10-17\",
    \"Statement\":[
      {\"Effect\":\"Allow\",\"Action\":[\"ecr:BatchGetImage\",\"ecr:GetDownloadUrlForLayer\"],\"Resource\":\"arn:aws:ecr:${REGION}:${ACCOUNT_ID}:repository/${ECR_REPO}\"},
      {\"Effect\":\"Allow\",\"Action\":\"ecr:GetAuthorizationToken\",\"Resource\":\"*\"},
      {\"Effect\":\"Allow\",\"Action\":[\"logs:CreateLogGroup\",\"logs:DescribeLogStreams\"],\"Resource\":\"arn:aws:logs:${REGION}:${ACCOUNT_ID}:log-group:/aws/bedrock-agentcore/runtimes/*\"},
      {\"Effect\":\"Allow\",\"Action\":\"logs:DescribeLogGroups\",\"Resource\":\"arn:aws:logs:${REGION}:${ACCOUNT_ID}:log-group:*\"},
      {\"Effect\":\"Allow\",\"Action\":[\"logs:CreateLogStream\",\"logs:PutLogEvents\"],\"Resource\":\"arn:aws:logs:${REGION}:${ACCOUNT_ID}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*\"},
      {\"Effect\":\"Allow\",\"Action\":[\"xray:PutTraceSegments\",\"xray:PutTelemetryRecords\",\"xray:GetSamplingRules\",\"xray:GetSamplingTargets\"],\"Resource\":\"*\"},
      {\"Effect\":\"Allow\",\"Action\":\"cloudwatch:PutMetricData\",\"Resource\":\"*\",\"Condition\":{\"StringEquals\":{\"cloudwatch:namespace\":\"bedrock-agentcore\"}}},
      {\"Effect\":\"Allow\",\"Action\":[\"bedrock:InvokeModel\",\"bedrock:InvokeModelWithResponseStream\"],\"Resource\":[\"arn:aws:bedrock:*::foundation-model/*\",\"arn:aws:bedrock:${REGION}:${ACCOUNT_ID}:*\"]}
    ]
  }"

sleep 10

# ── Step 4: Create AgentCore Runtime ──────────────────────────
echo -e "\n▶ Step 4/5: AgentCore Runtime..."
AGENT_ARN=""
RUNTIMES=$(aws bedrock-agentcore-control list-agent-runtimes --region "${REGION}" --query "agentRuntimes[?agentRuntimeName=='${AGENT_NAME}'].agentRuntimeArn" --output text 2>/dev/null || echo "")
if [ -n "${RUNTIMES}" ] && [ "${RUNTIMES}" != "None" ]; then
  AGENT_ARN="${RUNTIMES}"
  echo "  Exists: ${AGENT_ARN}"
else
  AGENT_ARN=$(aws bedrock-agentcore-control create-agent-runtime \
    --agent-runtime-name "${AGENT_NAME}" \
    --agent-runtime-artifact "{\"containerConfiguration\":{\"containerUri\":\"${ECR_URI}:latest\"}}" \
    --network-configuration '{"networkMode":"PUBLIC"}' \
    --role-arn "${ROLE_ARN}" \
    --region "${REGION}" \
    --query 'agentRuntimeArn' --output text)
  echo "  Created: ${AGENT_ARN}"

  echo "  Waiting for ACTIVE status..."
  for i in $(seq 1 30); do
    STATUS=$(aws bedrock-agentcore-control get-agent-runtime \
      --agent-runtime-id "${AGENT_ARN}" --region "${REGION}" \
      --query 'status' --output text 2>/dev/null || echo "CREATING")
    printf "    [%02d/30] %s\n" "$i" "${STATUS}"
    [ "${STATUS}" = "ACTIVE" ] && break
    sleep 10
  done
fi

ENCODED_ARN=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${AGENT_ARN}', safe=''))")
AGENT_ENDPOINT="https://bedrock-agentcore.${REGION}.amazonaws.com/runtimes/${ENCODED_ARN}/invocations"

# ── Step 5: SAM deploy (all infrastructure) ────────────────────
echo -e "\n▶ Step 5/5: Deploying SAM stack..."
cd "${SCRIPT_DIR}"
sam build --use-container 2>/dev/null || sam build
sam deploy \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --resolve-s3 \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    "ParameterKey=AgentCoreEndpoint,ParameterValue=${AGENT_ENDPOINT}" \
    "ParameterKey=AgentName,ParameterValue=${AGENT_NAME}" \
    "ParameterKey=ScheduleExpression,ParameterValue='${SCHEDULE_EXPR}'" \
    "ParameterKey=SchedulePayload,ParameterValue='${SCHEDULE_PAYLOAD}'" \
  --no-confirm-changeset

# ── Read outputs ───────────────────────────────────────────────
get_output() {
  aws cloudformation describe-stacks --stack-name "${STACK_NAME}" --region "${REGION}" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text
}

POOL_ID=$(get_output CognitoUserPoolId)
CLIENT_ID=$(get_output CognitoAppClientId)
EVENT_BUS_NAME="${STACK_NAME}-bus"

# ── Done ──────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════════════"
echo "  ✅ Deployment complete!"
echo ""
echo "  AgentCore ARN:  ${AGENT_ARN}"
echo "  Schedule:       ${STACK_NAME}-schedule (${SCHEDULE_EXPR})"
echo "  EventBus:       ${EVENT_BUS_NAME}"
echo "  Connection:     ${STACK_NAME}-connection"
echo "  API Dest:       ${STACK_NAME}-dest"
echo ""
echo "  Test manually:"
echo "    aws events put-events --entries '[{"
echo "      \"EventBusName\":\"${EVENT_BUS_NAME}\","
echo "      \"Source\":\"scheduler.agentcore\","
echo "      \"DetailType\":\"ScheduledAgentInvocation\","
echo "      \"Detail\":\"{\\\"prompt\\\":\\\"Hello from manual test!\\\"}\"}"
echo "    }]' --region ${REGION}"
echo ""
echo "  Manage schedule:"
echo "    aws scheduler get-schedule --name ${STACK_NAME}-schedule --region ${REGION}"
echo "    aws scheduler update-schedule --name ${STACK_NAME}-schedule --state DISABLED ... # pause"
echo ""
echo "  ⚠️  Configure AgentCore JWT authorizer:"
echo "    Discovery URL:     https://cognito-idp.${REGION}.amazonaws.com/${POOL_ID}/.well-known/openid-configuration"
echo "    Allowed Audiences: ${CLIENT_ID}"
echo "    Allowed Clients:   ${CLIENT_ID}"
echo "    Allowed Scopes:    ${AGENT_NAME}/invoke"
echo "══════════════════════════════════════════════════════════"
