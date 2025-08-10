# NVIDIA NeMo Guardrails Integration
Example for integrating Strands Agent with [NVIDIA NeMo Guardrails](https://developer.nvidia.com/nemo-guardrails) for configurable, rule-based content filtering and conversation flow control.

NeMo Guardrails provides a toolkit for creating customizable guardrails that can control and guide AI conversations through predefined rules and flows.

## Prerequisites

1. Python 3.8+ installed
2. NeMo Guardrails package (included in requirements.txt)
3. Basic understanding of NeMo configuration files

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/), so that you can run the NVIDIA NeMo server seperately.

You may also need build-essentials installed to run the NVIDIA NeMo server
```
sudo apt-get update
sudo apt-get install -y build-essentials
```

## Usage

1. Start the NeMo Guardrails server:
```bash
cd nemo-guardrail-examples
uvx nemoguardrails server --config .
```

2. In another terminal, run the Strands Agent example:
```bash
python main.py
```

The agent will communicate with the NeMo Guardrails server to validate and filter content based on the configured rules.
On first pass, the nvivida server will download a local model.

## Files

- `main.py` - Strands Agent with NeMo Guardrails integration
- `guardrail.py` - NeMo Guardrails client implementation
- `requirements.txt` - Python dependencies including nemoguardrails
- `nemo-guardrail-examples/` - Configuration directory for NeMo server
  - `my-first-guardrail/` - Example guardrail configuration
    - `config.yml` - Main configuration file
    - `rails/` - Custom rails definitions

## How It Works

The example runs NeMo Guardrails in server mode and communicates via REST API. The Strands Agent sends messages to the NeMo server for validation before processing.

### Server API
Send POST requests to: `http://127.0.0.1:8000/v1/chat/completions`

Payload format:
```json
{
    "config_id": "my-first-guardrail",
    "messages": [{
        "role": "user",
        "content": "hello there"
    }]
}
```
Where `config_id` matches guardrai name.

## Configuration

The `config.yml` file defines:
- Conversation flows and rules
- Input/output filtering policies  
- Custom rails for specific use cases
- Integration with external services

See the [NeMo Guardrails documentation](https://docs.nvidia.com/nemo/guardrails/) for detailed configuration options.