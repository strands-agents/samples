#!/bin/bash

# AI Triage Agent Deployment Script

set -e

STACK_NAME="triage-demo"
REGION="us-west-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ASSETS_BUCKET="triage-assets-$ACCOUNT_ID"
PACKAGE_NAME="triage-ui-package.zip"
TEMP_DIR="triage_temp"

if [ $? -ne 0 ] || [ -z "$ACCOUNT_ID" ] || [ "$ACCOUNT_ID" = "None" ]; then
    echo "❌ Failed to get AWS Account ID. Please check your AWS credentials and network connectivity."
    echo "Error: $ACCOUNT_ID"
    exit 1
fi

echo "🚀 Deploying AI Triage Agent..."

# Create assets bucket if not exists
echo "🪣 Creating assets bucket..."
if ! aws s3 ls s3://$ASSETS_BUCKET >/dev/null 2>&1; then
    aws s3 mb s3://$ASSETS_BUCKET --region $REGION
else
    echo "Bucket already exists, skipping creation"
fi

# Create UI package
echo "📦 Creating UI package..."
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Copy project files
rsync -av --progress ../ "$TEMP_DIR/triage-agents/" \
  --exclude='node_modules' \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='build' \
  --exclude='dist' \
  --exclude='.git' \
  --exclude='deploy'

# Create start script
cat > "$TEMP_DIR/triage-agents/start.sh" << 'EOF'
#!/bin/bash
echo "🚀 Starting AI Triage Agent..."

cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
python3 main.py &
BACKEND_PID=$!

cd ../frontend
npm install
npm start &
FRONTEND_PID=$!

echo "✅ System started!"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8000"

trap 'kill $BACKEND_PID $FRONTEND_PID' EXIT
wait
EOF

chmod +x "$TEMP_DIR/triage-agents/start.sh"

# Create ZIP package
echo "🗜️ Creating ZIP package..."
cd "$TEMP_DIR"
zip -r "../$PACKAGE_NAME" . -q
cd ..

# Upload package to S3
echo "📤 Uploading package to S3..."
aws s3 cp "$PACKAGE_NAME" s3://$ASSETS_BUCKET/$PACKAGE_NAME

# Build and upload frontend
echo "🏗️ Building frontend..."
cd ../frontend
npm install
npm run build

cd ../deploy

# Deploy CloudFormation stack
echo "☁️ Deploying CloudFormation stack..."
aws cloudformation deploy \
  --template-file triage-demo.yaml \
  --stack-name $STACK_NAME \
  --region $REGION \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    InstanceType=t3.large \
    VolumeSize=20 \
    AssetsBucketName=$ASSETS_BUCKET \
    AssetsPackageName=$PACKAGE_NAME

# Get outputs
echo "📋 Getting stack outputs..."
FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' \
  --output text)

CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
  --output text)

DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
  --output text)

# Create S3 bucket policy
echo "🔐 Creating S3 bucket policy..."
cat > bucket-policy.json << EOF
{
  "Statement": [
    {
      "Action": "s3:GetObject",
      "Effect": "Allow",
      "Resource": "arn:aws:s3:::$FRONTEND_BUCKET/*",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::$ACCOUNT_ID:distribution/$DISTRIBUTION_ID"
        }
      }
    }
  ]
}
EOF

aws s3api put-bucket-policy --bucket $FRONTEND_BUCKET --policy file://bucket-policy.json
rm bucket-policy.json

cd ../frontend
echo "📤 Uploading frontend to S3..."
aws s3 sync build/ s3://$FRONTEND_BUCKET/ --delete

cd ../deploy

# Cleanup
rm -rf "$TEMP_DIR" "$PACKAGE_NAME"

echo "✅ Deployment complete!"
echo "🌐 Application URL: $CLOUDFRONT_URL"
echo "🔗 API URL: $CLOUDFRONT_URL/api"
echo "🪣 Assets Bucket: $ASSETS_BUCKET"