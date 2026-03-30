#!/bin/bash
# Deep Research Assistant - Setup Script

set -e

echo "Setting up Deep Research Assistant..."

# Create virtual environment
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "Virtual environment created."
fi

# Activate and install dependencies
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "Dependencies installed."

# Check prerequisites
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "Warning: AWS credentials not configured. Run 'aws configure'."
fi

if [ -z "$EXA_API_KEY" ]; then
    echo "Warning: EXA_API_KEY not set. Get one at https://dashboard.exa.ai/api-keys"
fi

echo ""
echo "Setup complete. To run:"
echo "  source .venv/bin/activate"
echo "  export EXA_API_KEY= "
echo "  python deep_research_assistant.py"
