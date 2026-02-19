#!/bin/bash
# Deep Research Assistant - Setup with Full Observability

set -e

echo "🔭 Setting up Deep Research Assistant with AWS CloudWatch Observability..."
echo ""

# Create virtual environment
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Virtual environment created"
fi

# Activate and install dependencies
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✅ Dependencies installed (including OpenTelemetry)"

# Create .env from observability template 
cp .env-obs.example .env
echo "✅ Created .env file from observability template"

# Setup CloudWatch resources and OTEL configuration
echo ""
echo "📊 Setting up CloudWatch observability..."
python setup-observability.py

# Check prerequisites (same approach as setup-new.sh)
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "⚠️  AWS credentials not configured. Run 'aws configure'."
fi

if [ -z "$EXA_API_KEY" ]; then
    echo "⚠️  EXA_API_KEY not set. Get one at https://dashboard.exa.ai/api-keys"
    echo "   After setup, run: export EXA_API_KEY=your-key-here"
fi

echo ""
echo "🎉 Setup complete. To run with observability:"
echo ""
echo "  source .venv/bin/activate"
echo "  export EXA_API_KEY=your-key-here  # If not already set"
echo "  source .env  # Ensure your env varibales are loaded correctly"
echo "  Enable Transaction Search in CloudWatch (see Pre requisites in Readme)"
echo "  opentelemetry-instrument python deep_research_assistant.py \"your query\""
echo ""
echo "View traces in CloudWatch > GenAI Observability  (exa-deep-research)"