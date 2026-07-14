# DaoXE OpenAI-compatible provider with Strands Agents

Use [DaoXE](https://daoxe.com) as an OpenAI-compatible multi-model gateway from Strands Agents via `strands.models.openai.OpenAIModel`.

DaoXE exposes Chat Completions at `https://daoxe.com/v1`. Model IDs are **account-scoped** (use your dashboard catalog or `GET /v1/models`). DaoXE is multi-protocol (OpenAI-compatible + Anthropic Messages where available); this sample covers the OpenAI path for Strands.

> **Availability:** DaoXE is **not available in mainland China**.

## Tutorial Details

| Information | Details |
|-------------|---------|
| **Strands Features** | OpenAI-compatible model provider (`OpenAIModel`) |
| **Agent Pattern** | Single agent |
| **Tools** | Custom tools (`current_time`, `current_weather`) |
| **Model** | Account-scoped model ID on DaoXE (`https://daoxe.com/v1`) |

## Key Concepts

- **OpenAI compatibility**: Point Strands `OpenAIModel` at DaoXE with `base_url=https://daoxe.com/v1`.
- **Account-scoped model IDs**: Do not hardcode a public model list; use your DaoXE account catalog.
- **Multi-protocol gateway**: Same gateway also supports other protocol surfaces for non-Strands clients; this sample uses OpenAI Chat Completions only.

## Prerequisites

- Python 3.10+
- DaoXE account and API key from [daoxe.com](https://daoxe.com)
- A model ID enabled on your DaoXE account
- Network access from a region where DaoXE is available (not mainland China)

## Getting Started

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**

   ```bash
   export DAOXE_API_KEY="your-daoxe-api-key"
   export DAOXE_MODEL_ID="your-account-model-id"
   ```

3. **Run the CLI sample:**

   ```bash
   python daoxe_openai_agent.py
   ```

4. **Or open the notebook:**

   ```bash
   jupyter notebook daoxe-openai-agent.ipynb
   ```

## Project Structure

```
04-daoxe-model/
├── daoxe_openai_agent.py      # CLI script
├── daoxe-openai-agent.ipynb   # Interactive notebook
├── requirements.txt
├── README.md
```

## Affiliation

Community contribution from a DaoXE maintainer (`seven7763`). Examples: https://github.com/seven7763/DaoXE-AI

## References

- [DaoXE](https://daoxe.com)
- [DaoXE-AI client examples](https://github.com/seven7763/DaoXE-AI)
- [Strands community: DaoXE model provider](https://strandsagents.com/) (community model providers catalog)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
