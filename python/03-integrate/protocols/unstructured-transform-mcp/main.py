"""Unstructured Transform MCP + Strands Agent sample.

This sample connects a Strands Agent to the hosted Unstructured Transform MCP
server (https://mcp.transform.unstructured.io) over the streamable-http
transport and asks the agent to parse and chunk a public sample PDF.

The server's *asynchronous* document-processing pipeline works the same way
regardless of exact tool names: submit a file for processing, poll until
it's done, then fetch the rendered result; a separate tool mints an upload
URL for files that aren't already reachable over HTTPS. Unstructured adds
tools and capabilities to this server as they ship new features, so this
sample discovers the live toolset at connect time (see main()) rather than
hardcoding names, and asks the agent to match tools to each step by
description.

Because the pipeline is async, this sample gives the agent explicit
instructions to submit the job, poll for completion, and then fetch the
rendered results - rather than relying on a single free-form prompt. This
makes the async job lifecycle visible in the console output.

Prerequisites:
    - An Unstructured API key (see the Transform get-started page at
      https://transform.unstructured.io/get-started) exported as UNSTRUCTURED_API_KEY.
    - AWS credentials with Amazon Bedrock model access configured in your
      environment (see .env.example).

Docs: https://docs.unstructured.io/transform/overview

Usage:
    uv run main.py
"""

import os
import sys

from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient

# Hosted Unstructured Transform MCP server (streamable-http transport).
TRANSFORM_MCP_URL = "https://mcp.transform.unstructured.io"

# Bedrock model used to drive the agent. Requires model access to be enabled
# in your AWS account/region; see the README Prerequisites section.
MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

# A small, stable, publicly-reachable PDF used purely to demonstrate the
# pipeline end-to-end. Swap this for any https:// URL, or use the
# upload-URL tool first if you want to process a local file.
SAMPLE_PDF_URL = "https://arxiv.org/pdf/1706.03762"


def build_mcp_client(api_key: str) -> MCPClient:
    """Create an MCPClient wired up to the hosted Transform MCP server.

    Transform MCP supports two auth modes: browser OAuth/OIDC, and an
    API-key mode for headless frameworks like this one, where the key is
    passed as a bearer token in the Authorization header.
    """

    def create_transport():
        return streamablehttp_client(
            url=TRANSFORM_MCP_URL,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    return MCPClient(create_transport)


def main() -> None:
    api_key = os.environ.get("UNSTRUCTURED_API_KEY")
    if not api_key:
        print(
            "ERROR: UNSTRUCTURED_API_KEY is not set.\n"
            "Get a key from the Transform get-started page (https://transform.unstructured.io/get-started) "
            "and export it, e.g.:\n\n"
            "    export UNSTRUCTURED_API_KEY=<your-key>\n",
            file=sys.stderr,
        )
        sys.exit(1)

    mcp_client = build_mcp_client(api_key)

    with mcp_client:
        # Discover the tools Transform MCP exposes live, rather than
        # hardcoding names that Unstructured may rename or add to.
        tools = mcp_client.list_tools_sync()
        print(f"Connected to Transform MCP. Discovered {len(tools)} tool(s):")
        for tool in tools:
            print(f"  - {tool.tool_name}")
        print()

        agent = Agent(model=MODEL_ID, tools=tools)

        # Give the agent explicit steps so the async job lifecycle
        # (submit -> poll -> fetch) is exercised deterministically, rather
        # than leaving the whole flow to the model's discretion.
        prompt = f"""
Process this document using the Transform tools available to you: {SAMPLE_PDF_URL}

Check the tools available to you and use whichever ones match the steps
below by description, since exact tool names may change over time.

Follow these steps exactly:
1. Submit the file (file_refs=["{SAMPLE_PDF_URL}"]) for processing, with
   stages configured for a partition (strategy "auto") followed by a chunk
   stage with default settings. This returns a job ID.
2. Check the job's status repeatedly (waiting a few seconds between
   checks) until it reports as complete.
3. Fetch the job's results with output_format="md".
4. Summarize the first two chunks of the returned markdown in 2-3 sentences.
"""

        response = agent(prompt)
        print("\n--- Agent response ---")
        print(response)


if __name__ == "__main__":
    main()
