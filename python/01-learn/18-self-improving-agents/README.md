# Self-Improving Agents with Strands

Go from a 20-line Strands agent to a fully autonomous, self-improving agent deployed on Amazon Bedrock AgentCore Runtime. Across six progressive steps, the agent learns to **create its own tools**, **rewrite its own system prompt**, **remember across sessions**, **work autonomously in the background**, and finally **deploy itself to production**.

![From 20 lines of Python to a deployed autonomous agent](./images/hero.svg)

> Adapted from the AWS New York Summit 2026 builders session **AIM308 — "Using Strands to build fully autonomous, self-improving AI agents."** Origin: re:Invent 2025 AIM426.

## Tutorial Details

| Information          | Details                                                                                  |
|----------------------|------------------------------------------------------------------------------------------|
| **Strands Features** | `Agent`, `@tool`, `load_tools_from_directory`, dynamic system prompt, ambient background loop |
| **Agent Pattern**    | Single self-improving agent (extends itself step by step)                                |
| **Native Tools**     | `shell`, `file_write`                                                                     |
| **Custom Tools**     | `system_prompt` (self-modification), `calculator` (example of a self-written tool)        |
| **Memory**           | Amazon Bedrock AgentCore Memory (semantic, per-actor)                                     |
| **Complexity**       | Beginner → Advanced (progressive)                                                         |
| **Model Provider**   | Amazon Bedrock — Claude Sonnet 4.5 (`global.anthropic.claude-opus-4-8`)                  |
| **SDK Used**         | Strands Agents SDK, `bedrock-agentcore`                                                   |

## The core pattern: Agent → Model → Tools

Every step reuses this one loop. Once you grok **Agent · Model · Tools**, everything else is a variation.

![Strands agent loop — the model decides whether to call a tool; the observation feeds back until a final answer](./images/agent-loop.svg)

## The 6-step journey

| # | Step | Capability you add | New code | Runtime | Visual |
|---|------|--------------------|----------|---------|--------|
| 0 | [`step-00-hello`](./code/step-00-hello/)             | Baseline agent (one model, one tool)        | 20 lines | Local | [▶](./images/module-1-hello.svg) |
| 1 | [`step-01-tools`](./code/step-01-tools/)             | **Self-extending** — hot-reload `./tools/*.py` | +10 | Local | [▶](./images/module-2-hot-reload.svg) |
| 2 | [`step-02-system-prompt`](./code/step-02-system-prompt/) | **Self-modifying** — rewrites its own prompt | +40 | Local | [▶](./images/module-3-self-modify.svg) |
| 3 | [`step-03-memory`](./code/step-03-memory/)           | **Self-learning** — AgentCore Memory         | +30 | Local | [▶](./images/module-4-memory.svg) |
| 4 | [`step-04-ambient`](./code/step-04-ambient/)         | **Autonomous** — ambient + scheduler         | +50 | Local | [▶](./images/module-5-ambient.svg) |
| 5 | [`step-05-deploy`](./code/step-05-deploy/)           | **Deployed** — AgentCore Runtime ARN         | +15 | **Cloud** ☁ | [▶](./images/module-6-deploy.svg) |

## What you'll learn

1. 🛠️ **Agents can create their own tools** while running — no restart, no redeploy (`load_tools_from_directory=True`).
2. ✏️ **Agents can rewrite their own system prompt** — permanently changing their own behavior, persisted to disk.
3. 🧠 **Agents can learn from every interaction** — using Amazon Bedrock AgentCore Memory.
4. 🌙 **Agents can run autonomously in the background** — exploring a topic while you're idle, then injecting findings.
5. 🚀 **Agents can deploy themselves to production** — on Amazon Bedrock AgentCore Runtime.

## Prerequisites

- Python **3.10+** and `pip`
- AWS account with [Amazon Bedrock model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html) enabled for Claude Sonnet 4.5 in `us-east-1`
- AWS credentials configured (`aws configure` or environment variables)
- For steps 3–5: [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/) access
- For step 5 deploy: Node.js 20+ (the new [`@aws/agentcore`](https://github.com/aws/agentcore-cli) CLI)

## Run any step locally

Each step is self-contained and builds on the previous one:

```bash
cd code/step-00-hello
pip install -r requirements.txt
python agent.py "hello, what can you do?"
```

Then progress through the steps:

```bash
cd ../step-01-tools     && pip install -r requirements.txt && python agent.py
cd ../step-02-system-prompt && pip install -r requirements.txt && python agent.py
# ...etc
```

### Steps 3–5: create the memory store first

```bash
cd code/step-03-memory
pip install -r requirements.txt
python create_memory.py                       # prints a BEDROCK_AGENTCORE_MEMORY_ID
export BEDROCK_AGENTCORE_MEMORY_ID=<the-id>
python agent.py
```

### Step 5: deploy to AgentCore Runtime

```bash
cd code/step-05-deploy
export BEDROCK_AGENTCORE_MEMORY_ID=<your-memory-id>
./deploy.sh                                    # creates + deploys via @aws/agentcore CLI
```

Then invoke the deployed agent from anywhere:

```bash
export AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:...:runtime/aim308_research_agent-XYZ
python invoke.py "what do you remember about me?"
```

## Notebook walkthroughs

Prefer interactive? Each step has a click-through Jupyter notebook in [`notebooks/`](./notebooks/):

| Notebook | Step |
|----------|------|
| [`00_hello_agent.ipynb`](./notebooks/00_hello_agent.ipynb)     | Hello agent |
| [`01_self_extending.ipynb`](./notebooks/01_self_extending.ipynb) | Self-extending tools |
| [`02_self_modifying.ipynb`](./notebooks/02_self_modifying.ipynb) | Self-modifying prompt |
| [`03_memory.ipynb`](./notebooks/03_memory.ipynb)               | AgentCore Memory |
| [`04_autonomous.ipynb`](./notebooks/04_autonomous.ipynb)       | Ambient autonomy |
| [`05_deploy.ipynb`](./notebooks/05_deploy.ipynb)               | Deploy to AgentCore |

## See it run

Each step was recorded live against the real Strands runtime + Claude. The animated SVG recordings and replayable [asciinema](https://asciinema.org/) `.cast` files live in [`casts/`](./casts/) (replay locally with `asciinema play casts/01-self-extending.cast`).

| Cast | Step | What it shows |
|------|------|---------------|
| [`00-hello`](./casts/00-hello.svg)             | 0 | 20-line agent; one autonomous `shell` tool call |
| [`01-self-extending`](./casts/01-self-extending.svg) | 1 | Agent writes `tools/password_generator.py` mid-run, then uses it |
| [`02-self-modifying`](./casts/02-self-modifying.svg) | 2 | Agent rewrites its own prompt → haiku mode; `.prompt` persists |
| [`03-memory`](./casts/03-memory.svg)           | 3 | AgentCore Memory recall across sessions |
| [`04-ambient`](./casts/04-ambient.svg)         | 4 | Background ambient thread + finding injection |
| [`05-deploy`](./casts/05-deploy.svg)           | 5 | `agentcore create → add agent → deploy → invoke` |

## Project structure

```
18-self-improving-agents/
├── README.md
├── code/                          # Commit-by-commit agent source (what you RUN)
│   ├── step-00-hello/             # 20-line baseline
│   ├── step-01-tools/             # + self-extending tools (hot-reload)
│   ├── step-02-system-prompt/     # + self-modification (.prompt persistence)
│   ├── step-03-memory/            # + AgentCore Memory (semantic recall)
│   ├── step-04-ambient/           # + autonomous background work + scheduler
│   └── step-05-deploy/            # + AgentCore Runtime deployment
├── notebooks/                     # Interactive click-through mirror of each step
├── images/                        # Animated SVG diagrams (hero + per-step)
└── casts/                         # asciinema recordings (.cast + animated .svg)
```

## Additional Resources

- [Strands Agents SDK](https://github.com/strands-agents/sdk-python)
- [Strands Agents Tools](https://github.com/strands-agents/tools)
- [Strands Documentation](https://strandsagents.com)
- [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/)
- [`@aws/agentcore` CLI](https://github.com/aws/agentcore-cli)

## Disclaimer

This sample is provided for educational and demonstration purposes only. It is not intended for production use without further development, testing, and hardening. For production deployments, implement appropriate content filtering and safety measures, follow security best practices, conduct thorough testing, and review configurations for your specific requirements.
