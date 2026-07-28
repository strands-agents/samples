"""Unstructured Transform MCP + Strands Agent sample.

This sample connects a Strands Agent to the hosted Unstructured Transform MCP
server (https://mcp.transform.unstructured.io) over the streamable-http
transport and asks the agent to parse and chunk a public sample PDF.

Transform MCP exposes an *asynchronous* document-processing pipeline through
four tools:

    start_transform_job(file_refs, stages) -> job_id
    check_job_status(job_id)     -> status
    get_job_results(job_id, output_format) -> rendered output
    request_file_upload_url()          -> presigned URL for local files

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
# pipeline end-to-end. Swap this for any https:// URL, or use
# request_file_upload_url() first if you want to process a local file.
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
        # Discover the tools Transform MCP exposes (start_transform_job,
        # check_job_status, get_job_results,
        # request_file_upload_url).
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
Process this document using the Transform tools: {SAMPLE_PDF_URL}

Follow these steps exactly:
1. Call start_transform_job with file_refs=["{SAMPLE_PDF_URL}"] and stages
   configured for a partition (strategy "auto") followed by a chunk stage
   with default settings. This returns a job_id.
2. Call check_job_status with that job_id repeatedly (waiting a few
   seconds between calls) until the status indicates the job is complete.
3. Call get_job_results with the job_id and output_format="md".
4. Summarize the first two chunks of the returned markdown in 2-3 sentences.
"""

        response = agent(prompt)
        print("\n--- Agent response ---")
        print(response)


if __name__ == "__main__":
    main()
