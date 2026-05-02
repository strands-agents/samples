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
echo -e "\n▶ Step 1/7: ECR repository..."
aws ecr describe-repositories --repository-names "${ECR_REPO}" --region "${REGION}" >/dev/null 2>&1 \
  || aws ecr create-repository --repository-name "${ECR_REPO}" --region "${REGION}" --output text >/dev/null

aws ecr get-login-password --region "${REGION}" \
  | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com" 2>/dev/null

# ── Step 2: Build & push container ─────────────────────────────
echo -e "\n▶ Step 2/7: Building agent container (ARM64)..."
docker buildx build --platform linux/arm64 \
  -t "${ECR_URI}:latest" --push "${SCRIPT_DIR}/agent"

# ── Step 3: AgentCore execution role ───────────────────────────
echo -e "\n▶ Step 3/7: AgentCore execution role..."
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
echo -e "\n▶ Step 4/7: AgentCore Runtime..."
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

# ── Step 5: SAM deploy (Cognito + EventBridge bus) ─────────────
echo -e "\n▶ Step 5/7: Deploying SAM stack..."
cd "${SCRIPT_DIR}"
sam build --use-container 2>/dev/null || sam build
sam deploy \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --resolve-s3 \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    "ParameterKey=AgentCoreEndpoint,ParameterValue=${AGENT_ENDPOINT}" \
    "ParameterKey=AgentName,ParameterValue=${AGENT_NAME}" \
    "ParameterKey=ScheduleExpression,ParameterValue='${SCHEDULE_EXPR}'" \
    "ParameterKey=SchedulePayload,ParameterValue='${SCHEDULE_PAYLOAD}'" \
  --no-confirm-changeset

# ── Step 6: Wire up Connection + API Destination + Rule ────────
echo -e "\n▶ Step 6/7: Creating EventBridge Connection, API Destination, and Rule..."

get_output() {
  aws cloudformation describe-stacks --stack-name "${STACK_NAME}" --region "${REGION}" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text
}

POOL_ID=$(get_output CognitoUserPoolId)
CLIENT_ID=$(get_output CognitoAppClientId)
TOKEN_ENDPOINT=$(get_output CognitoTokenEndpoint)
EVENT_BUS_ARN=$(get_output EventBusArn)

CLIENT_SECRET=$(aws cognito-idp describe-user-pool-client \
  --user-pool-id "${POOL_ID}" \
  --client-id "${CLIENT_ID}" \
  --region "${REGION}" \
  --query 'UserPoolClient.ClientSecret' --output text)

CONNECTION_NAME="${STACK_NAME}-connection"
DEST_NAME="${STACK_NAME}-dest"
RULE_NAME="${STACK_NAME}-rule"
EVENT_BUS_NAME="${STACK_NAME}-bus"

# Create/update Connection
echo "  Creating connection..."
aws events create-connection \
  --name "${CONNECTION_NAME}" \
  --authorization-type OAUTH_CLIENT_CREDENTIALS \
  --auth-parameters "{
    \"OAuthParameters\": {
      \"AuthorizationEndpoint\": \"${TOKEN_ENDPOINT}\",
      \"HttpMethod\": \"POST\",
      \"ClientParameters\": {
        \"ClientID\": \"${CLIENT_ID}\",
        \"ClientSecret\": \"${CLIENT_SECRET}\"
      },
      \"OAuthHttpParameters\": {
        \"BodyParameters\": [
          {\"Key\": \"grant_type\", \"Value\": \"client_credentials\", \"IsValueSecret\": false},
          {\"Key\": \"scope\", \"Value\": \"${AGENT_NAME}/invoke\", \"IsValueSecret\": false}
        ]
      }
    }
  }" \
  --region "${REGION}" 2>/dev/null \
|| aws events update-connection \
  --name "${CONNECTION_NAME}" \
  --authorization-type OAUTH_CLIENT_CREDENTIALS \
  --auth-parameters "{
    \"OAuthParameters\": {
      \"AuthorizationEndpoint\": \"${TOKEN_ENDPOINT}\",
      \"HttpMethod\": \"POST\",
      \"ClientParameters\": {
        \"ClientID\": \"${CLIENT_ID}\",
        \"ClientSecret\": \"${CLIENT_SECRET}\"
      },
      \"OAuthHttpParameters\": {
        \"BodyParameters\": [
          {\"Key\": \"grant_type\", \"Value\": \"client_credentials\", \"IsValueSecret\": false},
          {\"Key\": \"scope\", \"Value\": \"${AGENT_NAME}/invoke\", \"IsValueSecret\": false}
        ]
      }
    }
  }" \
  --region "${REGION}"

CONNECTION_ARN=$(aws events describe-connection --name "${CONNECTION_NAME}" --region "${REGION}" \
  --query 'ConnectionArn' --output text)

# Create/update API Destination
echo "  Creating API destination..."
aws events create-api-destination \
  --name "${DEST_NAME}" \
  --connection-arn "${CONNECTION_ARN}" \
  --invocation-endpoint "${AGENT_ENDPOINT}" \
  --http-method POST \
  --invocation-rate-limit-per-second 10 \
  --region "${REGION}" 2>/dev/null \
|| aws events update-api-destination \
  --name "${DEST_NAME}" \
  --connection-arn "${CONNECTION_ARN}" \
  --invocation-endpoint "${AGENT_ENDPOINT}" \
  --http-method POST \
  --invocation-rate-limit-per-second 10 \
  --region "${REGION}"

DEST_ARN=$(aws events describe-api-destination --name "${DEST_NAME}" --region "${REGION}" \
  --query 'ApiDestinationArn' --output text)

# IAM role for EventBridge -> API Destination
EB_ROLE_NAME="${STACK_NAME}-EBApiDestRole"
EB_ROLE_ARN=$(aws iam get-role --role-name "${EB_ROLE_NAME}" --query 'Role.Arn' --output text 2>/dev/null || echo "")
if [ -z "${EB_ROLE_ARN}" ] || [ "${EB_ROLE_ARN}" = "None" ]; then
  EB_ROLE_ARN=$(aws iam create-role \
    --role-name "${EB_ROLE_NAME}" \
    --assume-role-policy-document '{
      "Version":"2012-10-17",
      "Statement":[{"Effect":"Allow","Principal":{"Service":"events.amazonaws.com"},"Action":"sts:AssumeRole"}]
    }' --query 'Role.Arn' --output text)
fi
aws iam put-role-policy --role-name "${EB_ROLE_NAME}" \
  --policy-name InvokeApiDest \
  --policy-document "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":\"events:InvokeApiDestination\",\"Resource\":\"${DEST_ARN}\"}]}"
sleep 5

# Create Rule on the bus to route to API Destination
echo "  Creating rule..."
aws events put-rule \
  --name "${RULE_NAME}" \
  --event-bus-name "${EVENT_BUS_NAME}" \
  --event-pattern '{"source":["scheduler.agentcore"],"detail-type":["ScheduledAgentInvocation"]}' \
  --state ENABLED \
  --region "${REGION}" >/dev/null

DLQ_URL=$(get_output DLQUrl)
DLQ_ARN="arn:aws:sqs:${REGION}:${ACCOUNT_ID}:${STACK_NAME}-dlq"

aws events put-targets \
  --rule "${RULE_NAME}" \
  --event-bus-name "${EVENT_BUS_NAME}" \
  --targets "[{
    \"Id\": \"AgentCoreTarget\",
    \"Arn\": \"${DEST_ARN}\",
    \"RoleArn\": \"${EB_ROLE_ARN}\",
    \"InputTransformer\": {
      \"InputPathsMap\": {\"prompt\": \"$.detail.prompt\"},
      \"InputTemplate\": \"{\\\"prompt\\\": <prompt>}\"
    },
    \"DeadLetterConfig\": {\"Arn\": \"${DLQ_ARN}\"}
  }]" \
  --region "${REGION}" >/dev/null

# ── Step 7: EventBridge Scheduler -> EventBridge Bus ───────────
echo -e "\n▶ Step 7/7: Creating EventBridge Schedule..."

SCHEDULE_NAME="${STACK_NAME}-schedule"
SCHEDULER_ROLE_NAME="${STACK_NAME}-SchedulerRole"

# Scheduler execution role — needs permission to put events on the bus
SCHEDULER_ROLE_ARN=$(aws iam get-role --role-name "${SCHEDULER_ROLE_NAME}" --query 'Role.Arn' --output text 2>/dev/null || echo "")
if [ -z "${SCHEDULER_ROLE_ARN}" ] || [ "${SCHEDULER_ROLE_ARN}" = "None" ]; then
  SCHEDULER_ROLE_ARN=$(aws iam create-role \
    --role-name "${SCHEDULER_ROLE_NAME}" \
    --assume-role-policy-document '{
      "Version":"2012-10-17",
      "Statement":[{"Effect":"Allow","Principal":{"Service":"scheduler.amazonaws.com"},"Action":"sts:AssumeRole"}]
    }' --query 'Role.Arn' --output text)
fi

aws iam put-role-policy --role-name "${SCHEDULER_ROLE_NAME}" \
  --policy-name SchedulerPutEvents \
  --policy-document "{
    \"Version\":\"2012-10-17\",
    \"Statement\":[{
      \"Effect\":\"Allow\",
      \"Action\":\"events:PutEvents\",
      \"Resource\":\"${EVENT_BUS_ARN}\"
    }]
  }"

sleep 5

# Scheduler puts events onto the custom bus; the rule routes them to the API Destination
aws scheduler create-schedule \
  --name "${SCHEDULE_NAME}" \
  --schedule-expression "${SCHEDULE_EXPR}" \
  --flexible-time-window '{"Mode":"OFF"}' \
  --target "{
    \"Arn\": \"${EVENT_BUS_ARN}\",
    \"RoleArn\": \"${SCHEDULER_ROLE_ARN}\",
    \"EventBridgeParameters\": {
      \"Source\": \"scheduler.agentcore\",
      \"DetailType\": \"ScheduledAgentInvocation\"
    },
    \"Input\": \"{\\\"prompt\\\": \\\"You are triggered by a schedule. Report the current time and confirm you are running.\\\"}\"
  }" \
  --state ENABLED \
  --region "${REGION}" 2>/dev/null \
|| aws scheduler update-schedule \
  --name "${SCHEDULE_NAME}" \
  --schedule-expression "${SCHEDULE_EXPR}" \
  --flexible-time-window '{"Mode":"OFF"}' \
  --target "{
    \"Arn\": \"${EVENT_BUS_ARN}\",
    \"RoleArn\": \"${SCHEDULER_ROLE_ARN}\",
    \"EventBridgeParameters\": {
      \"Source\": \"scheduler.agentcore\",
      \"DetailType\": \"ScheduledAgentInvocation\"
    },
    \"Input\": \"{\\\"prompt\\\": \\\"You are triggered by a schedule. Report the current time and confirm you are running.\\\"}\"
  }" \
  --state ENABLED \
  --region "${REGION}"

# ── Done ──────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════════════"
echo "  ✅ Deployment complete!"
echo ""
echo "  AgentCore ARN:  ${AGENT_ARN}"
echo "  Schedule:       ${SCHEDULE_NAME} (${SCHEDULE_EXPR})"
echo "  EventBus:       ${EVENT_BUS_NAME}"
echo "  Connection:     ${CONNECTION_NAME}"
echo "  API Dest:       ${DEST_NAME}"
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
echo "    aws scheduler get-schedule --name ${SCHEDULE_NAME} --region ${REGION}"
echo "    aws scheduler update-schedule --name ${SCHEDULE_NAME} --state DISABLED ... # pause"
echo ""
echo "  ⚠️  Configure AgentCore JWT authorizer:"
echo "    Discovery URL:     https://cognito-idp.${REGION}.amazonaws.com/${POOL_ID}/.well-known/openid-configuration"
echo "    Allowed Audiences: ${CLIENT_ID}"
echo "    Allowed Clients:   ${CLIENT_ID}"
echo "    Allowed Scopes:    ${AGENT_NAME}/invoke"
echo "══════════════════════════════════════════════════════════"
