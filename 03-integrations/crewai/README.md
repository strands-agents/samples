# Strands Agent + CrewAI Integration

A simple integration that wraps **Strands Agents** as **CrewAI Tools**, enabling specialized mathematical conversions within multi-agent workflows.

## How It Works

**Strands Agent** → **CrewAI Custom Tool** → **CrewAI Agent** → **Task Execution**

1. Strands Agent handles mathematical conversions using AWS Bedrock
2. Custom `StrandsAgentConversionTool` wraps the Strands Agent as a CrewAI tool  
3. CrewAI agents use this tool within larger workflows
4. CrewAI orchestrates the entire process