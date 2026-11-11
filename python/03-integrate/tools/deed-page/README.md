# Publish Agent Output to the Web with deed.page

A Strands agent that writes a self-contained HTML page and publishes it to a public HTTPS URL with [deed.page](https://deed.page), so the result of a run is a link people can open rather than a file on the machine that ran the agent.

## Overview

### Sample Details

| Information            | Details                                                    |
|------------------------|------------------------------------------------------------|
| **Agent Architecture** | Single-agent                                               |
| **Native Tools**       | None                                                       |
| **Custom Tools**       | `publish_page`                                             |
| **MCP Servers**        | None in the main script; the remote deed.page MCP server is shown as an alternative below |
| **Use Case Vertical**  | Cross-industry (reports, briefs, status pages)             |
| **Complexity**         | Basic                                                      |
| **Model Provider**     | Amazon Bedrock                                             |
| **SDK Used**           | Strands Agents SDK                                         |

### How it works

```
user prompt ──► Agent (Bedrock) ──► publish_page(html, slug) ──► PUT https://deed.page/v1/sites?slug=...
                     ▲                         │
                     └──── "Published https://<slug>.deed.page/" ◄──┘
```

The agent writes the page, decides when it's ready, and calls `publish_page`. The tool sends one HTTP request and returns only the URL, slug, version and expiry to the agent.

### Key Features

- **Credential stays out of the model's context.** deed.page needs no account: the first publish returns an API token. The tool saves it to `~/.config/deed-page/token` (directory 700, file 600) and reuses it, but never returns it to the agent, so it can't end up in the conversation, a trace, or a published page.
- **Optional expiry.** `--ttl` sets `X-Ttl` on every publish for pages that are only needed for a while (a review, a daily status).
- **Deletion stays outside the agent loop.** The model can publish but not delete. `--delete <slug>` is a plain CLI path for cleanup.

## Prerequisites

- Python **3.10+**
- AWS CLI configured with credentials, and [model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html) enabled for Claude Sonnet 4.6 (override with `BEDROCK_MODEL_ID`)
- No deed.page signup or API key

## Setup

```bash
cd python/03-integrate/tools/deed-page
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Ask the agent for a page:

```bash
python publish_agent.py "Write a one-page brief on the history of the bicycle"
```

The agent replies with something like `https://bicycle-history-3f9a1c.deed.page/` and a one-line description.

Make the page expire after an hour:

```bash
python publish_agent.py --ttl 3600 "Turn these notes into a status page: build green, 2 open bugs, release Friday"
```

Check the publishing path without calling a model (useful before Bedrock access is set up):

```bash
python publish_agent.py --no-llm --ttl 600
```

This prints the URL, slug, version and `expires_at` of a small sample page.

## Cleanup

Pages stay online until they expire or you delete them:

```bash
python publish_agent.py --delete <slug>
```

The URL returns 404 afterwards. To stop using the saved token, delete `~/.config/deed-page/token` (or point `DEEDPAGE_TOKEN_FILE` somewhere else). Without a recovery email attached, a lost token can't be restored, so keep the file if you want to update or delete your pages later.

## Alternative: the remote MCP server

deed.page also runs a Streamable HTTP MCP server at `https://deed.page/mcp`. Strands can load it directly. `tool_filters` keeps the agent to the tools it needs:

```python
from strands import Agent
from strands.tools.mcp import MCPClient

headers = {"Authorization": f"Bearer {token}"}  # token from a previous publish
deed_page = MCPClient(
    url="https://deed.page/mcp",
    headers=headers,
    tool_filters={"allowed": ["publish_site", "get_site"]},
)

agent = Agent(tools=[deed_page])
agent("Write a one-page brief on the history of the bicycle and publish it")
```

Send the `Authorization` header from the start. On a first publish without a token, the MCP result includes the new token, which then sits in the model's context. That's the main reason this sample wraps the REST API in its own tool.

## Notes

- Anyone with the URL can open a published page. Don't publish secrets or personal data.
- The free plan's limits (number of sites, size per site) and the small attribution link on free pages are listed on [deed.page/pricing](https://deed.page/pricing). API reference: [deed.page/docs](https://deed.page/docs).
