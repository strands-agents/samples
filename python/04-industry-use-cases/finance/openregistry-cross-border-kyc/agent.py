"""Cross-border KYC / UBO chain-walking agent built with Strands.

Connects an Anthropic Claude (or any Bedrock-hosted) model to the hosted
OpenRegistry MCP server (https://openregistry.sophymarine.com/mcp), which
proxies 27 national company registries directly to AI agents — UK Companies
House, Germany Handelsregister, France Sirene+RNE, Italy InfoCamere via EU
BRIS, Spain BORME, Korea OPENDART, plus 21 more. Every tool call is a live
query against the upstream government API.

Anonymous tier requires no signup or API key, so this sample runs out of the
box with only the standard Bedrock IAM / region setup.
"""

from __future__ import annotations

import os

from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient

OPENREGISTRY_MCP_URL = os.environ.get(
    "OPENREGISTRY_MCP_URL", "https://openregistry.sophymarine.com/mcp"
)
OPENREGISTRY_TOKEN = os.environ.get("OPENREGISTRY_TOKEN")  # optional, paid tiers

SYSTEM_PROMPT = (
    "You are a cross-border KYC / due-diligence assistant with live access to "
    "27 national company registries via the OpenRegistry MCP server. When asked "
    "about a company, identify the relevant jurisdiction (ISO 3166-1 alpha-2, "
    "e.g. 'gb' for UK, 'de' for Germany, 'fr' for France) and use the OpenRegistry "
    "tools to look it up. Always pass jurisdiction='<code>' explicitly. Quote the "
    "registry's own field names verbatim — never normalise PSC `nature_of_control` "
    "values. When walking corporate ownership chains across borders, recurse "
    "jurisdiction by jurisdiction until you reach an individual or hit an "
    "AML-gated register. If a tool returns HTTP 501 with an `alternative_url`, "
    "surface that URL — it signals a CJEU C-37/20-restricted register "
    "(DE / ES / IT / NL / LU / AT / MT / PT) which only AML-obliged entities can "
    "query. Always cite the registry and the company identifier you looked up so "
    "the user can verify against the government source."
)


def make_mcp_client() -> MCPClient:
    """Build a Strands MCPClient pointed at the OpenRegistry hosted server."""

    headers = (
        {"Authorization": f"Bearer {OPENREGISTRY_TOKEN}"} if OPENREGISTRY_TOKEN else None
    )

    def transport():
        return streamablehttp_client(OPENREGISTRY_MCP_URL, headers=headers)

    return MCPClient(transport)


def main() -> None:
    user_prompt = (
        "Walk Revolut Ltd's PSC chain (UK Companies House company number 08804411) "
        "across jurisdictions until you reach an individual or hit an AML-gated "
        "register. Cite the registry and identifier for each hop, and quote the "
        "upstream `nature_of_control` strings verbatim."
    )

    with make_mcp_client() as client:
        tools = client.list_tools_sync()
        print(f"Discovered {len(tools)} tools from OpenRegistry")

        agent = Agent(
            system_prompt=SYSTEM_PROMPT,
            tools=tools,
        )
        response = agent(user_prompt)
        print(response)


if __name__ == "__main__":
    main()
