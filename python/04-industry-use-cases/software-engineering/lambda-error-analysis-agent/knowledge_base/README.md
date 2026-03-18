# Knowledge Base Documentation

This folder contains reference documentation that feeds the Amazon Bedrock Knowledge Base used by the Error Analyzer Agent.

## Purpose

When the AI agent analyzes Lambda errors, it searches this knowledge base to:
- Identify error patterns
- Find root causes
- Provide specific recommendations
- Reference AWS service error codes
- Apply best practices

## Contents

- **`lambda-error-patterns.md`** - Common Lambda failure patterns and analysis approaches
- **`aws-service-errors.md`** - Comprehensive AWS service error codes and solutions
- **`troubleshooting-guide.md`** - Step-by-step debugging methodology
- **`best-practices.md`** - Lambda development best practices
- **`common-errors.md`** - Common Lambda errors and solutions

## How It Works

1. **Deployment**: CDK automatically syncs this folder to S3
2. **Indexing**: Bedrock Knowledge Base indexes the content with vector embeddings
3. **Search**: Agent uses `search_knowledge_base()` tool to query relevant information
4. **Analysis**: Agent combines KB results with source code and logs for comprehensive analysis

## Adding New Content

To add new error patterns or troubleshooting guides:

1. Create or update markdown files in this folder
2. Deploy the stack: `npm run deploy`
3. Knowledge Base automatically syncs new content
4. Agent can immediately search the updated knowledge

## Best Practices for KB Content

- **Be specific**: Include exact error messages and codes
- **Provide solutions**: Always include actionable recommendations
- **Use examples**: Code snippets help the agent understand context
- **Stay current**: Update with new AWS service features and error patterns
- **Be concise**: Clear, focused content improves search relevance
