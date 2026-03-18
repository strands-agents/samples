#!/bin/bash

# Financial Advisor Prerequisites Deployment Script
# This script sets up the required AWS resources for the Financial Advisor application

set -e  # Exit on any error

echo "🚀 Starting Financial Advisor Prerequisites Deployment..."
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "application/prerequisites/prereqs_config.yaml" ]; then
    echo "❌ Error: prereqs_config.yaml not found. Please run this script from the genai_powered_financial_advisor_tools directory."
    exit 1
fi

# Verify required scripts exist
if [ ! -f "application/prerequisites/bedrock_knowledge_base_setup.py" ]; then
    echo "❌ Error: bedrock_knowledge_base_setup.py not found in application/prerequisites/"
    exit 1
fi

if [ ! -f "application/prerequisites/athena_database_setup.py" ]; then
    echo "❌ Error: athena_database_setup.py not found in application/prerequisites/"
    exit 1
fi

# Deploy Knowledge Base
echo ""
echo "📚 Step 1: Deploying Knowledge Base..."
echo "--------------------------------------"
python application/prerequisites/bedrock_knowledge_base_setup.py --mode create

if [ $? -eq 0 ]; then
    echo "✅ Knowledge Base deployment completed successfully"
else
    echo "❌ Knowledge Base deployment failed"
    exit 1
fi

# Deploy Athena Database and Tables
echo ""
echo "🗄️  Step 2: Deploying Database and Tables using Amazon Athena..."
echo "---------------------------------------------------------------"
python application/prerequisites/athena_database_setup.py --mode create

if [ $? -eq 0 ]; then
    echo "✅ Athena database deployment completed successfully"
else
    echo "❌ Athena database deployment failed"
    exit 1
fi

echo ""
echo "🎉 All prerequisites deployed successfully!"
echo "=================================================="
echo "📋 Next steps:"
echo "   1. Verify resources in AWS Console"
echo "   2. Check prereqs_config.yaml for updated values"
echo "   3. Run your Financial Advisor application:  streamlit run application/app.py"
echo ""