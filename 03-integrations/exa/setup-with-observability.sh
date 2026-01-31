#!/bin/bash
# Deep Research Assistant - Setup with Full Observability

set -e

echo "🔭 Setting up Deep Research Assistant with AWS CloudWatch Observability..."
echo "="*70
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

# Create .env from example if doesn't exist
if [ ! -f ".env" ]; then
    cp .env-obs.example .env
    echo "✅ Created .env file from template"
fi


# Setup CloudWatch resources and OTEL configuration
echo ""
echo "📊 Setting up CloudWatch observability..."
python setup-observability.py

# Check if EXA_API_KEY is set
source .env 2>/dev/null || true
if [ -z "$EXA_API_KEY" ]; then
    echo ""
    echo "="*70
    echo "⚠️  ACTION REQUIRED: Add your Exa API key to the .env file"
    echo "="*70
fi

echo ""
echo "🎉 Setup complete with observability!"
echo ""
echo "Next steps:"
echo "  1. Ensure your Exa API key is in .env file and your env variables are loaded correctly in your environment"
echo "  2. Enable Transaction Search in CloudWatch (see instructions in Readme)"
echo "  3. Run with observability:"
echo ""
echo "     source .venv/bin/activate"
echo "     opentelemetry-instrument python deep_research_assistant.py  "[Add your single query]""
echo ""
echo "  View traces after a few minutes in CloudWatch > GenAI Observability Dashboard "
echo "  Look for : exa-deep-research"