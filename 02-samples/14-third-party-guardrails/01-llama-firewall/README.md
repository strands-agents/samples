# Llama Firewall Integration
Example for integrating Strands Agent with [Meta's Llama Firewall](https://meta-llama.github.io/PurpleLlama/LlamaFirewall/) for local model-based input filtering and safety checks.

Llama Firewall uses local models (via HuggingFace) to check user input for potentially harmful content before it reaches your AI agent.

## Prerequisites

1. Sign up to [HuggingFace](https://huggingface.co/) and get an API key
2. Request access to [Llama-Prompt-Guard-2-86M](https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M) (usually approved within minutes)
3. Python 3.8+ installed

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure Llama Firewall:
```bash
llamafirewall configure
```
Enter your HuggingFace API token when prompted.

## Usage

Run the example:
```bash
python main.py
```

The agent will use Llama Firewall to filter user input before processing. Potentially harmful prompts will be blocked.

## Files

- `main.py` - Strands Agent with Llama Firewall hook integration
- `guardrail.py` - Llama Firewall implementation and filtering logic  
- `requirements.txt` - Python dependencies including llamafirewall

## How It Works

The example uses Strands Agent hooks to intercept messages and run them through Llama Firewall's safety checks. If content is flagged as potentially harmful, it's blocked before reaching the LLM.

