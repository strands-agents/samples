# Cross-Border KYC Agent — Strands + OpenRegistry MCP

A Strands agent with live access to **27 national company registries** via the [OpenRegistry](https://openregistry.sophymarine.com) hosted MCP server — UK Companies House, Germany Handelsregister, France Sirene + RNE, Italy InfoCamere via EU BRIS, Spain BORME, Korea OPENDART, plus 21 more.

Demonstrates `strands.tools.mcp.MCPClient` connected to a remote Streamable-HTTP MCP server (no local stdio process), which is the canonical shape for production AI-agent integrations against third-party SaaS data tools.

## Use case

Cross-border **Know-Your-Business** (KYB) and **beneficial-ownership** (UBO) chain walking for compliance / fraud / AML pipelines. Given any company, the agent recursively walks its corporate ownership across jurisdictions until it reaches an individual or hits an AML-gated register — citing every hop back to the upstream government source.

## Run it

```bash
cd python/04-industry-use-cases/finance/openregistry-cross-border-kyc
pip install -r requirements.txt

# Default model is Bedrock; configure your region / IAM as usual.
export AWS_REGION=us-west-2

python agent.py
```

The `agent.py` ships a starter prompt that walks **Revolut Ltd** (UK Companies House `08804411`) across borders. Edit `user_prompt` in `main()` to try other entities.

## All 30 jurisdictions covered

The single MCP endpoint covers every jurisdiction below. ⚠ = CJEU C-37/20–restricted UBO register (the agent surfaces `alternative_url` honestly). 💳 = paid-tier only.

| ISO | Country | Native registry |
|---|---|---|
| `GB` | United Kingdom | Companies House |
| `IE` | Ireland | Companies Registration Office (CRO) |
| `FR` | France | INSEE Sirene + RNE |
| `DE` ⚠ | Germany | Handelsregister |
| `IT` ⚠ | Italy | Registro delle imprese (via EU BRIS) |
| `ES` ⚠ | Spain | BORME |
| `NL` ⚠ | Netherlands | KVK Handelsregister |
| `BE` | Belgium | KBO/BCE (Crossroads Bank for Enterprises) |
| `PL` | Poland | KRS (Krajowy Rejestr Sądowy) |
| `CZ` | Czechia | ARES |
| `FI` | Finland | PRH (YTJ) |
| `NO` | Norway | Brønnøysundregistrene (Enhetsregisteret) |
| `IS` | Iceland | Fyrirtækjaskrá (Skatturinn) |
| `CH` | Switzerland | Zefix (Federal Registry of Commerce) |
| `LI` | Liechtenstein | Handelsregister Liechtenstein (Amt für Justiz) |
| `MC` | Monaco | RCI (Répertoire du Commerce et de l'Industrie) |
| `IM` | Isle of Man | IoM Companies Registry |
| `CY` | Cyprus | DRCOR |
| `KR` | South Korea | OPENDART (FSS Electronic Disclosure System) |
| `TW` | Taiwan | GCIS (Ministry of Economic Affairs) |
| `HK` | Hong Kong SAR | Companies Registry |
| `MY` | Malaysia | SSM (Suruhanjaya Syarikat Malaysia) |
| `AU` | Australia | ABR (ABN Lookup) |
| `NZ` | New Zealand | NZ Companies Office |
| `CA` | Canada (federal) | Corporations Canada (CBCA, ISED) |
| `CA-BC` | Canada · British Columbia | OrgBook BC |
| `CA-NT` | Canada · Northwest Territories | CROS-RSEL (NWT Department of Justice) |
| `MX` | Mexico | PSM (Sistema Electrónico de Publicaciones de Sociedades Mercantiles) |
| `KY` 💳 | Cayman Islands | CIMA (Regulated Entities Register) |
| `RU` | Russia | ЕГРЮЛ / ЕГРИП (FNS) + ГИР БО |

For the live capability matrix per jurisdiction (which tools each register supports, native ID format, quirks), call `list_jurisdictions` from the running agent.

## OpenRegistry tier

The default URL (`https://openregistry.sophymarine.com/mcp`) uses the **anonymous tier** — no signup, no API key. Limits: 20 req/min/IP, 3-country fan-out per 60s. For batch onboarding, complete the OAuth 2.1 flow at [openregistry.sophymarine.com/account](https://openregistry.sophymarine.com/account) and pass the token via `OPENREGISTRY_TOKEN`.

## Statutorily restricted registers

After CJEU C-37/20 (Nov 2022), the EU UBO registers in **DE / ES / IT / NL / LU / AT / MT / PT** became access-restricted to AML-obliged entities. OpenRegistry returns HTTP 501 with `alternative_url` for those — the agent's system prompt teaches it to surface the URL rather than substitute aggregator data, so the AML wall is honest.

## What's in scope (and what's not)

**In scope**: company profile, officers, PSCs, shareholders, charges, filings, raw documents (PDF / iXBRL / XBRL), accounts, name availability across 27 jurisdictions.

**Out of scope** (not in OpenRegistry): credit scores, sanctions list screening, PEP screening, US private-company financials. Pair with a separate sanctions MCP if you need those.

## License

MIT (matches the rest of `strands-agents/samples`). OpenRegistry docs are CC-BY-4.0.
