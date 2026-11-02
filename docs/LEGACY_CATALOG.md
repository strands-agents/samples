# Legacy catalog ledger

The broad examples catalog was removed from the default branch so this repository can rebuild around fewer, complete end-to-end applications.

All previous source remains available in the immutable pre-cleanup commit [`2776a90cc510aa3a79163ac9847f7a4088a20daa`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa). This preserves attribution and gives maintainers a source when rebuilding a useful pattern. Removing files from the default branch reduces the checked-out tree; it does not rewrite or shrink Git history.

The two workshop trees remain in place. Three application seeds also remain and will be reviewed independently:

- `python/05-technical-use-cases/fastapi-strands-production-starter`
- `python/07-ux-demos/human-in-the-loop-approval-agent`
- `typescript/02-deploy/02-nextjs-vercel-adapter`

Disposition meanings:

- `merge`: retain useful patterns only when a complete replacement application is built.
- `docs`: focused teaching material whose canonical home should be the main documentation.
- `labs`: experimental or higher-risk material that needs a Labs-specific review.
- `archive`: historical material with no current promotion plan.

These labels describe future intent. This cleanup does not claim that content has already been migrated to another repository.

| Former path | Disposition | Follow-up |
|---|---|---|
| [`python/02-deploy/01-lambda`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/02-deploy/01-lambda) | merge | Future customer-service application deployment profile |
| [`python/02-deploy/02-fargate`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/02-deploy/02-fargate) | merge | Future customer-service application deployment profile |
| [`python/02-deploy/03-agentcore`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/02-deploy/03-agentcore) | merge | Future customer-service application deployment profile |
| [`python/02-deploy/04-agentcore-multi-agent/01-a2a-orchestration`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/02-deploy/04-agentcore-multi-agent/01-a2a-orchestration) | merge | Future A2A multi-agent application |
| [`python/03-integrate/databases/aurora-dsql`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/03-integrate/databases/aurora-dsql) | docs | Database integration documentation |
| [`python/03-integrate/databases/neptune`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/03-integrate/databases/neptune) | docs | Database integration documentation |
| [`python/03-integrate/databases/supabase`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/03-integrate/databases/supabase) | docs | Database integration documentation |
| [`python/03-integrate/guardrails/alice-wonderfence`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/03-integrate/guardrails/alice-wonderfence) | docs | Guardrail integration documentation |
| [`python/03-integrate/guardrails/llama-firewall`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/03-integrate/guardrails/llama-firewall) | docs | Guardrail integration documentation |
| [`python/03-integrate/guardrails/nvidia-nemo`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/03-integrate/guardrails/nvidia-nemo) | docs | Guardrail integration documentation |
| [`python/03-integrate/memory/zep-ai`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/03-integrate/memory/zep-ai) | docs | Memory integration documentation |
| [`python/03-integrate/observability/arize`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/03-integrate/observability/arize) | docs | Observability integration documentation |
| [`python/03-integrate/protocols/a2a`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/03-integrate/protocols/a2a) | docs | Protocol integration documentation |
| [`python/03-integrate/protocols/a2a-native`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/03-integrate/protocols/a2a-native) | docs | Protocol integration documentation |
| [`python/03-integrate/tools/exa`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/03-integrate/tools/exa) | docs | Tool integration documentation |
| [`python/03-integrate/tools/nova-act`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/03-integrate/tools/nova-act) | docs | Tool integration documentation |
| [`python/03-integrate/tools/tavily`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/03-integrate/tools/tavily) | docs | Tool integration documentation |
| [`python/03-integrate/voice/nova-sonic`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/03-integrate/voice/nova-sonic) | archive | External implementation rather than a self-contained example |
| [`python/04-industry-use-cases/finance/finance-assistant-swarm-agent`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/04-industry-use-cases/finance/finance-assistant-swarm-agent) | archive | Historical industry example |
| [`python/04-industry-use-cases/finance/genai-powered-financial-advisor-tools`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/04-industry-use-cases/finance/genai-powered-financial-advisor-tools) | archive | Historical industry example |
| [`python/04-industry-use-cases/finance/personal-finance-assistant`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/04-industry-use-cases/finance/personal-finance-assistant) | archive | Historical industry example |
| [`python/04-industry-use-cases/finance/whatsapp-fintech`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/04-industry-use-cases/finance/whatsapp-fintech) | archive | Historical industry example |
| [`python/04-industry-use-cases/healthcare/medical-document-processing-assistant`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/04-industry-use-cases/healthcare/medical-document-processing-assistant) | archive | Historical industry example |
| [`python/04-industry-use-cases/logistics/custom-orchestration-airline-assistant`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/04-industry-use-cases/logistics/custom-orchestration-airline-assistant) | merge | Future airline application with integrated evaluation |
| [`python/04-industry-use-cases/marketing/ai-ads-generation-agent-with-crypto-payments`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/04-industry-use-cases/marketing/ai-ads-generation-agent-with-crypto-payments) | archive | Historical industry example |
| [`python/04-industry-use-cases/marketing/startup-advisor-mcp`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/04-industry-use-cases/marketing/startup-advisor-mcp) | archive | Historical industry example |
| [`python/04-industry-use-cases/productivity/multi-modal-email-assistant-agent`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/04-industry-use-cases/productivity/multi-modal-email-assistant-agent) | archive | Historical industry example |
| [`python/04-industry-use-cases/productivity/personal-assistant`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/04-industry-use-cases/productivity/personal-assistant) | archive | Historical industry example |
| [`python/04-industry-use-cases/productivity/research-agent`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/04-industry-use-cases/productivity/research-agent) | labs | Broad shell, filesystem, Python, and AWS authority |
| [`python/04-industry-use-cases/productivity/scrum-master-assistant`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/04-industry-use-cases/productivity/scrum-master-assistant) | archive | Historical industry example |
| [`python/04-industry-use-cases/retail/restaurant-assistant`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/04-industry-use-cases/retail/restaurant-assistant) | merge | Future customer-service application |
| [`python/04-industry-use-cases/software-engineering/amazon-dataprocessing-agent`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/04-industry-use-cases/software-engineering/amazon-dataprocessing-agent) | archive | Historical industry example |
| [`python/04-industry-use-cases/software-engineering/aws-assistant-mcp`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/04-industry-use-cases/software-engineering/aws-assistant-mcp) | archive | Historical industry example |
| [`python/04-industry-use-cases/software-engineering/aws-audit-assistant`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/04-industry-use-cases/software-engineering/aws-audit-assistant) | labs | Broad account access and generated-code execution |
| [`python/04-industry-use-cases/software-engineering/code-assistant`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/04-industry-use-cases/software-engineering/code-assistant) | archive | Historical industry example |
| [`python/04-industry-use-cases/software-engineering/data-warehouse-optimizer`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/04-industry-use-cases/software-engineering/data-warehouse-optimizer) | merge | Future data-operations application |
| [`python/04-industry-use-cases/software-engineering/lambda-error-analysis-agent`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/04-industry-use-cases/software-engineering/lambda-error-analysis-agent) | merge | Future operations application |
| [`python/04-industry-use-cases/software-engineering/sre-incident-response-agent`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/04-industry-use-cases/software-engineering/sre-incident-response-agent) | merge | Future operations application |
| [`python/05-technical-use-cases/pokemon-team-advisor`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/05-technical-use-cases/pokemon-team-advisor) | archive | Component-focused technical example |
| [`python/05-technical-use-cases/rag/agentic-rag/adaptive-structured-rag`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/05-technical-use-cases/rag/agentic-rag/adaptive-structured-rag) | merge | Future configurable knowledge/RAG application |
| [`python/05-technical-use-cases/rag/agentic-rag/corrective-rag`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/05-technical-use-cases/rag/agentic-rag/corrective-rag) | merge | Future configurable knowledge/RAG application |
| [`python/05-technical-use-cases/rag/agentic-rag/unstructured-structured-rag`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/05-technical-use-cases/rag/agentic-rag/unstructured-structured-rag) | merge | Future configurable knowledge/RAG application |
| [`python/05-technical-use-cases/steering/library-book-renewal-agent`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/05-technical-use-cases/steering/library-book-renewal-agent) | merge | Reuse policy, testing, and evaluation patterns |
| [`python/06-evaluate/ab-testing-models`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/06-evaluate/ab-testing-models) | merge | Future airline application evaluation |
| [`python/06-evaluate/built-in-evaluators`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/06-evaluate/built-in-evaluators) | docs | Evaluation documentation |
| [`python/06-evaluate/custom-evaluators`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/06-evaluate/custom-evaluators) | docs | Evaluation documentation |
| [`python/06-evaluate/dataset-generation`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/06-evaluate/dataset-generation) | docs | Evaluation documentation |
| [`python/06-evaluate/multi-agent-evaluation`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/06-evaluate/multi-agent-evaluation) | docs | Evaluation documentation |
| [`python/06-evaluate/multi-turn-actor-simulator`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/06-evaluate/multi-turn-actor-simulator) | docs | Evaluation documentation |
| [`python/06-evaluate/red-teaming`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/06-evaluate/red-teaming) | docs | Evaluation documentation |
| [`python/06-evaluate/trajectory-evaluation`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/06-evaluate/trajectory-evaluation) | docs | Evaluation documentation |
| [`python/07-ux-demos/ag-ui-copilotkit-integration`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/07-ux-demos/ag-ui-copilotkit-integration) | archive | Historical UI demonstration |
| [`python/07-ux-demos/hvac-data-analytics-agent`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/07-ux-demos/hvac-data-analytics-agent) | archive | Historical UI demonstration |
| [`python/07-ux-demos/slack-assistant`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/07-ux-demos/slack-assistant) | merge | Future channel-integration application |
| [`python/07-ux-demos/strands-playground`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/07-ux-demos/strands-playground) | labs | Powerful local tools require stronger hosted controls |
| [`python/07-ux-demos/streamlit-template`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/07-ux-demos/streamlit-template) | labs | Needs authentication, secure origins, and meaningful tests |
| [`python/07-ux-demos/triage-agent`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/07-ux-demos/triage-agent) | labs | High-stakes medical workflow requires domain safety review |
| [`python/07-ux-demos/video-games-sales-assistant`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/07-ux-demos/video-games-sales-assistant) | archive | Historical UI demonstration |
| [`python/08-edge/strands-spot-agent`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/python/08-edge/strands-spot-agent) | labs | Physical-device example requires deterministic safety controls |
| [`typescript/02-deploy/01-agentcore`](https://github.com/strands-agents/samples/tree/2776a90cc510aa3a79163ac9847f7a4088a20daa/typescript/02-deploy/01-agentcore) | archive | Outdated SDK and deployment baseline |

The unlisted `python/migration/langgraph` and `typescript/migration/langgraph` snippets were also removed. Their source remains in the same pre-cleanup commit.
