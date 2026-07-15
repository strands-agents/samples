# Model Providers in Strands Agents

Strands Agents takes a model-driven approach and is not tied to a single model or vendor. A *model provider* is the adapter that connects your agent to a specific model backend, and the SDK ships with providers for Amazon Bedrock, Anthropic, Ollama, LiteLLM, OpenAI, and more. This tutorial shows three of them in practice: running a model locally with Ollama, reaching Azure OpenAI through LiteLLM, and calling OpenAI models hosted on Amazon Bedrock through the Responses API.

## Tutorial Details

| Information          | Details                                                                 |
|:---------------------|:------------------------------------------------------------------------|
| Agent structure      | Single agent                                                            |
| Model providers      | `OllamaModel`, `LiteLLMModel`, `OpenAIResponsesModel`                   |
| Model backends       | Ollama (local), Azure OpenAI (via LiteLLM), OpenAI on Amazon Bedrock    |
| Strands features     | Swapping model providers, passing a configured model to `Agent`         |

## Key Concepts

- **Model provider**: A class such as `BedrockModel`, `OllamaModel`, or `LiteLLMModel` that adapts a model backend to the Strands `Agent`. You configure a provider instance and pass it as the `model` argument to `Agent`; the rest of your agent code stays the same.
- **Default provider**: If you create `Agent()` without a `model`, the SDK uses Amazon Bedrock with its default model. The other providers are opt-in — install the matching extra and construct the provider yourself.
- **Install extras**: Providers that need extra dependencies are published as pip extras, for example `strands-agents[ollama]`, `strands-agents[litellm]`, and `strands-agents[openai]`. Install the extra for the provider you want rather than the bare backend package, so you get a version the SDK supports.
- **Callback handlers**: For any provider you can attach [callback handlers](https://strandsagents.com/docs/user-guide/concepts/streaming/callback-handlers/) to intercept and process events during agent execution.

## Supported Model Providers

Strands Agents supports several model providers out of the box:

| Provider | Description |
|----------|-------------|
| [Amazon Bedrock](https://strandsagents.com/docs/user-guide/concepts/model-providers/amazon-bedrock/) | Default provider. Access foundation models from Anthropic, Meta, Amazon, and others through Amazon's managed service. |
| [Anthropic](https://strandsagents.com/docs/user-guide/concepts/model-providers/anthropic/) | Direct API access to Claude models. |
| [Ollama](https://strandsagents.com/docs/user-guide/concepts/model-providers/ollama/) | Run models locally for privacy or offline use. |
| [LiteLLM](https://strandsagents.com/docs/user-guide/concepts/model-providers/litellm/) | Unified interface for OpenAI, Azure OpenAI, Mistral, and many other providers. |
| [OpenAI](https://strandsagents.com/docs/user-guide/concepts/model-providers/openai/) | Direct access to OpenAI models, including the [Responses API](https://strandsagents.com/docs/user-guide/concepts/model-providers/openai-responses/). |
| [Amazon Nova](https://strandsagents.com/docs/user-guide/concepts/model-providers/amazon-nova/), [Google Gemini](https://strandsagents.com/docs/user-guide/concepts/model-providers/google/), [Mistral](https://strandsagents.com/docs/user-guide/concepts/model-providers/mistral/), [Writer](https://strandsagents.com/docs/user-guide/concepts/model-providers/writer/) | Additional providers built into the SDK. |
| [Custom Providers](https://strandsagents.com/docs/user-guide/concepts/model-providers/custom_model_provider/) | Build your own provider for specialized needs. |

## Prerequisites

- Python 3.10 or higher
- Basic understanding of Python
- Provider-specific requirements, called out in each sub-sample (Ollama installed locally, an Azure OpenAI deployment, or an AWS account with access to OpenAI models on Amazon Bedrock)

## Tutorial Structure

Each sub-sample is self-contained and has its own `requirements.txt`.

| Path | Description |
|------|-------------|
| [01-ollama-model/ollama_file_ops_agent.ipynb](./01-ollama-model/ollama_file_ops_agent.ipynb) | Run a model locally with `OllamaModel` and build a file-operations agent (`file_read`, `file_write`, `list_directory`). |
| [02-openai-model/openai-litellm-agent.ipynb](./02-openai-model/openai-litellm-agent.ipynb) | Reach an Azure OpenAI model through `LiteLLMModel` and give the agent `current_time` and `current_weather` tools. |
| [03-openai-responses-on-bedrock/openai-responses-agent.ipynb](./03-openai-responses-on-bedrock/openai-responses-agent.ipynb) | Call an OpenAI model hosted on Amazon Bedrock with `OpenAIResponsesModel` and the Responses API. |

## Getting Started

1. **Install dependencies** for the sub-sample you want to run:
   ```bash
   cd 01-ollama-model        # or: 02-openai-model, 03-openai-responses-on-bedrock
   pip install -r requirements.txt
   ```

2. **Run the notebook** in that folder and run the cells in order.

## Project Structure

```
03-model-providers/
├── 01-ollama-model/
│   ├── ollama_file_ops_agent.ipynb
│   ├── requirements.txt
│   ├── images/
│   └── sample_file/
├── 02-openai-model/
│   ├── openai-litellm-agent.ipynb
│   ├── requirements.txt
│   └── images/
├── 03-openai-responses-on-bedrock/
│   ├── openai-responses-agent.ipynb
│   ├── requirements.txt
│   └── images/
└── README.md
```
