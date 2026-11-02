<div align="center">
  <div>
    <a href="https://strandsagents.com">
      <picture>
        <source media="(prefers-color-scheme: dark)" srcset="https://strandsagents.com/latest/assets/wordmark-github-dark.svg">
        <img src="https://strandsagents.com/latest/assets/wordmark-github-light.svg" alt="Strands" width="320">
      </picture>
    </a>
  </div>

  <h1>
    Strands Agents Examples
  </h1>

  <h2>
    End-to-end applications and workshop curriculum for Strands Agents.
  </h2>

  <div align="center">
    <a href="https://github.com/strands-agents/samples/graphs/commit-activity"><img alt="GitHub commit activity" src="https://img.shields.io/github/commit-activity/m/strands-agents/samples"/></a>
    <a href="https://github.com/strands-agents/samples/issues"><img alt="GitHub open issues" src="https://img.shields.io/github/issues/strands-agents/samples"/></a>
    <a href="https://github.com/strands-agents/samples/pulls"><img alt="GitHub open pull requests" src="https://img.shields.io/github/issues-pr/strands-agents/samples"/></a>
    <a href="https://github.com/strands-agents/samples/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/strands-agents/samples"/></a>
    <a href="https://discord.gg/strands"><img alt="Strands Discord" src="https://img.shields.io/badge/Discord-Strands-5865F2?logo=discord&logoColor=white"/></a>
  </div>
  
  <p>
    <a href="https://strandsagents.com/">Documentation</a>
    ◆ <a href="https://github.com/strands-agents/samples">Samples</a>
    ◆ <a href="https://github.com/strands-agents/harness-sdk/tree/main/strands-cli">CLI</a>
    ◆ <a href="https://github.com/strands-agents/harness-sdk/tree/main/strands-mcp">MCP Server</a>
    <br>
    Harness (<a href="https://github.com/strands-agents/harness-sdk/tree/main/harness-py">Python</a>, <a href="https://github.com/strands-agents/harness-sdk/tree/main/harness-ts">TypeScript</a>)
    ◆ SDK (<a href="https://github.com/strands-agents/harness-sdk/tree/main/strands-py">Python</a>, <a href="https://github.com/strands-agents/harness-sdk/tree/main/strands-ts">TypeScript</a>)
    ◆ <a href="https://github.com/strands-agents/box">Box</a>
    ◆ <a href="https://github.com/strands-agents/shell">Shell</a>
    ◆ <a href="https://github.com/strands-agents/evals">Evals</a>
    ◆ <a href="https://github.com/strands-labs">Labs</a>
  </p>
</div>

This repository has two intentionally narrow purposes:

- Preserve the compatibility-sensitive Python and TypeScript workshop curriculum.
- Develop a small number of complete, deployable reference applications that combine multiple Strands components around a real user outcome.

Focused SDK concepts, provider setup, integrations, and evaluation techniques belong in the [Strands documentation](https://strandsagents.com/). Experimental, privileged, physical-device, and best-effort demonstrations belong in [Strands Labs](https://github.com/strands-labs).

The previous broad catalog is preserved at commit [`2776a90`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa). See the [legacy catalog ledger](./docs/LEGACY_CATALOG.md) for every removed example and its intended disposition.

The retained applications are starting points for focused follow-up work; they should not yet be treated as production-ready. Apply workload-specific security, privacy, testing, reliability, and operational controls before production use.

## Quick Start

<table>
<tr>
<td width="40%" valign="top">

### <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" width="24" height="24" alt="Python"/> Python

**Prerequisites:**
- Python 3.10 or higher
- pip package manager (not required when using the uv alternative below)
  - Verify with: `pip --version` or `pip3 --version`
  - Usually comes bundled with Python 3.4+ installers from python.org
  - If pip is missing, install using one of these methods:
    ```bash
    # Method 1 - Use Python's built-in module
    python -m ensurepip --upgrade

    # Method 2 - Download and run the official installer
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python get-pip.py
    ```

**Step 1: Create Virtual Environment**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

**Step 2: Install**
```bash
pip install strands-agents
```

This installs the core SDK, which is all the first agent below needs. Many samples need additional packages, so check each sample's README and `requirements.txt` or `pyproject.toml` before running it.

**Alternative: Use uv**

If you prefer [uv](https://docs.astral.sh/uv/), install it using the [official installation instructions](https://docs.astral.sh/uv/getting-started/installation/) and follow these steps instead of Steps 1 and 2 above.

Create a virtual environment:
```bash
uv venv
```

Activate it on macOS/Linux (bash or zsh):
```bash
source .venv/bin/activate
```

Or on Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks `Activate.ps1`, see Python's [Windows execution policy guidance](https://docs.python.org/3/library/venv.html#creating-virtual-environments) and follow any applicable organizational policies.

Then install the same package:
```bash
uv pip install strands-agents
```

**Your First Agent:**
```python
from strands import Agent

agent = Agent()
response = agent("Hello! Tell me a joke.")
print(response)
```

[Explore Python tutorials →](./python/01-learn/)

</td>
<td width="60%" valign="top">

### <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/typescript/typescript-original.svg" width="24" height="24" alt="TypeScript"/> TypeScript

**Prerequisites:**
- Node.js 18 or higher
- npm or yarn package manager

**Install:**
```bash
npm install @strands-agents/sdk
```

**Your First Agent:**
```typescript
import { Agent } from "@strands-agents/sdk";

async function main() {
    const agent = new Agent({
        systemPrompt: "You are a helpful assistant."
    });

    const response = await agent.invoke("Hello! Tell me a joke.");
    console.log(response.toString());
}

main();
```

[Explore TypeScript tutorials →](./typescript/01-learn/)

</td>
</tr>
</table>

### Model Provider Setup

Follow the instructions [here](https://strandsagents.com/docs/user-guide/sdk/model-providers/) to configure your model provider and model access.

## Repository contents

### Protected workshops

- [Python workshop](./python/01-learn/)
- [TypeScript workshop](./typescript/01-learn/)

These trees are pulled into an external workshop. Their paths, structure, and existing `samples.json` records are protected by CI. See the [workshop compatibility policy](./docs/WORKSHOP_COMPATIBILITY.md).

### Retained application seeds

- [FastAPI Strands production starter](./python/05-technical-use-cases/fastapi-strands-production-starter/)
- [Human-in-the-loop approval agent](./python/07-ux-demos/human-in-the-loop-approval-agent/)
- [Next.js Vercel adapter](./typescript/02-deploy/02-nextjs-vercel-adapter/)

Each application will be reviewed and improved in its own pull request. New examples should solve a distinct end-to-end outcome rather than demonstrate a single component.

The documentation website currently consumes `samples.json`. The compatibility manifest retains workshop records, so the website must filter the exact `python/01-learn/` and `typescript/01-learn/` prefixes before the next catalog deployment.

## Contributing ❤️

See the [Contributing Guide](CONTRIBUTING.md). New standalone examples are paused while the retained applications are rebuilt and the catalog contract is simplified.

## Stay in touch with the team
Come meet the Strands team and other users on [**Discord**](https://discord.com/invite/strands)

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.
