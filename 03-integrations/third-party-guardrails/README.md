# Third Party Guardrails
Contains conceptual examples using Strands Agent hooks to integrate with third-party guardrail services for content filtering, safety checks, and compliance monitoring.

Many of these examples require additional setup, but have free tiers.

The following examples all use the `MessageAddedEvent`, which is called every time a message is added to the agent.
This means the same callback is used for inputs to an LLM, and responses from the LLM.

It's recommended to use the most relevant [hook](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/hooks/) for your use case.

Event messages are follow the [Amazon Bedrock runtime message format](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Message.html). At present, [there isn't an elegant way to extract the latest string from the message object](https://github.com/strands-agents/sdk-python/discussions/620).

## Available Examples

| Example | Service | Description | Setup Requirements |
|---------|---------|-------------|-------------------|
| [01-llama-firewall](./01-llama-firewall/) | [Meta's Llama Firewall](https://meta-llama.github.io/PurpleLlama/LlamaFirewall/) | Local model-based input filtering using Llama-Prompt-Guard-2-86M | HuggingFace account, API key, model access request |
| [02-guardrailai](./02-guardrailai/) | [Guardrails AI](https://www.guardrailsai.com/) | Cloud-based guardrails with toxic language detection | Guardrails AI account, API key, hub guardrail installation |
| [03-nvidia-nemo](./03-nvidia-nemo/) | [NVIDIA NeMo Guardrails](https://developer.nvidia.com/nemo-guardrails) | Server-based guardrails with configurable rules | Local NeMo server setup, configuration files |

## Getting Started

Each example contains:
- `README.md` - Detailed setup and configuration instructions
- `main.py` - Strands Agent implementation with guardrail integration
- `guardrail.py` - Guardrail-specific implementation logic
- `requirements.txt` - Python dependencies

Choose the guardrail service that best fits your use case and follow the setup instructions in the respective example directory.
