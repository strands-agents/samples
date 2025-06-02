# Using Amazon Neptune with the Strands Agent SDK

This directory contains several examples of how to use Strands Agent SDK with Amazon Neptune.

Within this directory there are several example Python files:

* [memory_kg_mcp_example.py](./memory_kg_mcp_example.py) - This example demonstrates how to use the [Amazon Neptune Memory MCP server](https://github.com/aws-samples/amazon-neptune-generative-ai-samples/tree/main/neptune-mcp-servers/neptune-memory) and [Perplexity MCP server](https://deepwiki.com/ppl-ai/modelcontextprotocol) to research a topic and generate a knowledge graph from the researched information.
* [query_mcp_example.py](./query_mcp_example.py) - This example demonstrates how to use the [Amazon Neptune MCP server](https://github.com/awslabs/mcp/tree/main/src/amazon-neptune-mcp-server) to generate and run queries against a Neptune Database or Neptune Analytics instance.
* [use_aws_example.py](./use_aws_example.py) - This example demonstrates how to use the `use_aws` tool to perform control or data plane actions against a Neptune Database or Neptune Analytics instance. 

## Getting started

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Configure AWS credentials, follow instructions [here](https://strandsagents.com/latest/user-guide/quickstart/#configuring-credentials).
3. Run the example using `uv run <SELECT EXAMPLE FILE TO RUN>`.


