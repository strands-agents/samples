# Bedrock Managed Knowledge Base Support

## Changes
- Added managed KB sample application demonstrating end-to-end workflow
- New sample: create managed KB, add data source, sync, and retrieve
- Retrieval sample uses `managedSearchConfiguration` as default
- Added `AgenticRetrieveStream` sample for agentic retrieval pattern
- Existing VECTOR samples preserved with clear labeling

## Design
- VECTOR is the default; MANAGED samples added as alternatives
- Samples demonstrate both Python (boto3) and JavaScript (AWS SDK) paths
- AgenticRetrieveStream sample shows streaming agentic retrieval
- Backward compatible: existing VECTOR samples unchanged, new managed samples added alongside

## API Shapes
- KB Creation: `type: MANAGED` + `managedKnowledgeBaseConfiguration.embeddingModelType: MANAGED`
- Data Source: `type: MANAGED_KNOWLEDGE_BASE_CONNECTOR`
- Retrieval: `managedSearchConfiguration` (not `vectorSearchConfiguration`)
- Agentic: `AgenticRetrieveStream` with `foundationModelType: MANAGED`, `rerankingModelType: MANAGED`

## Configuration
| Variable | Description | Default |
|---|---|---|
| KNOWLEDGE_BASE_TYPE | MANAGED or VECTOR | VECTOR |
| USE_AGENTIC_RETRIEVAL | Enable agentic retrieval | true |
| KNOWLEDGE_BASE_ID | KB ID | (required) |

## SDK Requirements
- boto3 >= 1.43 for managed search and agentic retrieval
- JS SDK >= 3.750.0 for managed KB support

## Required IAM Permissions
```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:Retrieve",
    "bedrock:AgenticRetrieveStream"
  ],
  "Resource": "arn:aws:bedrock:<region>:<account-id>:knowledge-base/<kb-id>"
}
```
