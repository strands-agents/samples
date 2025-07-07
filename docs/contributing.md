# Contributing to Strands Agent Patterns

Thank you for your interest in contributing to the Strands Agent Patterns repository! This guide will help you create high-quality patterns that benefit the entire Strands community.

## Pattern Contribution Process

### 1. Planning Your Pattern

Before you start coding, consider:

- **Scope**: Focus on 2-4 service integrations maximum
- **Uniqueness**: Ensure your pattern adds value not covered by existing patterns
- **Reusability**: Design for broad applicability across different use cases
- **Documentation**: Plan comprehensive documentation from the start

### 2. Using Pattern Templates

Start with the appropriate template from `_templates/`:

```bash
# Copy the basic agent template
cp -r _templates/basic-agent agent-patterns/your-pattern-name

# For multi-agent systems
cp -r _templates/multi-agent agent-patterns/your-pattern-name

# For AWS integrations
cp -r _templates/aws-integration agent-patterns/your-pattern-name
```

### 3. Naming Convention

Follow the service-based naming convention:

- **Good**: `websearch-agent`, `bedrock-knowledgebase-dynamodb`, `streamlit-chatbot`
- **Bad**: `my-agent`, `awesome-ai`, `pattern1`

**Format**: `service1-service2-usecase` or `technology-usecase`

### 4. Pattern Structure

Ensure your pattern follows this structure:

```
pattern-name/
├── README.md                 # Complete documentation
├── pattern-metadata.json     # Structured metadata
├── src/
│   ├── agent.py             # Main implementation
│   ├── tools/               # Custom tools (if any)
│   └── prompts/             # Prompt templates (if any)
├── requirements.txt          # Python dependencies
├── tests/
│   ├── test_agent.py        # Unit tests
│   └── test_integration.py  # Integration tests
├── examples/
│   ├── basic_usage.py       # Simple example
│   └── advanced_usage.py    # Complex scenario
├── prereqs/                 # Infrastructure setup (if needed)
│   ├── deploy.sh           # Deployment script
│   └── cleanup.sh          # Cleanup script
└── docs/
    └── architecture.md      # Detailed architecture (optional)
```

## Documentation Requirements

### README.md Template

Your README must include:

1. **Title and Description**: Clear, concise explanation
2. **Requirements**: All prerequisites listed
3. **Deployment Instructions**: Step-by-step setup
4. **How it Works**: Architecture explanation with diagrams
5. **Testing**: Example queries and expected outputs
6. **Cleanup**: Resource cleanup instructions
7. **Next Steps**: Enhancement suggestions
8. **Documentation Links**: Relevant Strands and AWS docs

### Pattern Metadata

Update `pattern-metadata.json` with accurate information:

```json
{
  "title": "Your Pattern Title",
  "description": "Brief description of what this pattern does",
  "category": "basic-agents|multi-agent-systems|knowledge-retrieval|aws-integrations|tool-integrations|ui-ux-patterns",
  "complexity": "beginner|intermediate|advanced",
  "tags": ["relevant", "tags", "for", "discovery"],
  "frameworks": ["strands-agents"],
  "llm_providers": ["bedrock", "openai", "anthropic"],
  "aws_services": ["service1", "service2"],
  "author": {
    "name": "Your Name",
    "github": "your-github-username",
    "linkedin": "your-linkedin-profile"
  },
  "created_date": "YYYY-MM-DD",
  "metrics": {
    "estimated_cost": "$X/month",
    "performance": "Xms average response time"
  },
  "learning_objectives": [
    "What users will learn from this pattern"
  ]
}
```

## Code Quality Standards

### Python Code Requirements

1. **Type Hints**: Use type hints for all function parameters and returns
2. **Docstrings**: Include comprehensive docstrings for all functions and classes
3. **Error Handling**: Implement proper exception handling with meaningful error messages
4. **Logging**: Use appropriate logging levels and messages
5. **Code Style**: Follow PEP 8 standards

### Example Code Structure

```python
#!/usr/bin/env python3
"""
Pattern Title

Brief description of what this pattern demonstrates.
"""

import logging
from typing import Dict, Any, Optional
from strands import Agent, tool

# Configure logging
logging.getLogger("strands").setLevel(logging.INFO)

@tool
def custom_tool(param: str) -> Dict[str, Any]:
    """
    Description of what this tool does.
    
    Args:
        param: Description of the parameter
        
    Returns:
        Dict containing the tool result
        
    Raises:
        ValueError: When param is invalid
    """
    try:
        # Implementation here
        result = {"status": "success", "data": param}
        return result
    except Exception as e:
        logging.error(f"Error in custom_tool: {e}")
        return {"status": "error", "message": str(e)}

def create_agent() -> Agent:
    """Create and configure the agent."""
    system_prompt = """Your system prompt here."""
    
    agent = Agent(
        system_prompt=system_prompt,
        tools=[custom_tool]
    )
    
    return agent

if __name__ == "__main__":
    agent = create_agent()
    # Interactive loop or example usage
```

## Testing Requirements

### Unit Tests

Create tests for all custom tools and functions:

```python
import pytest
from src.agent import custom_tool, create_agent

def test_custom_tool():
    """Test the custom tool with valid input."""
    result = custom_tool("test input")
    assert result["status"] == "success"
    assert result["data"] == "test input"

def test_agent_creation():
    """Test that the agent can be created successfully."""
    agent = create_agent()
    assert agent is not None
    assert len(agent.tools) > 0
```

### Integration Tests

Test the complete workflow:

```python
def test_agent_workflow():
    """Test the complete agent workflow."""
    agent = create_agent()
    response = agent("test query")
    assert response is not None
    # Add specific assertions based on expected behavior
```

## Infrastructure Patterns

### AWS Resource Management

If your pattern requires AWS resources:

1. **Infrastructure as Code**: Use CloudFormation, CDK, or Terraform
2. **Deployment Scripts**: Provide automated deployment scripts
3. **Cleanup Scripts**: Always include resource cleanup
4. **Cost Estimation**: Provide accurate cost estimates
5. **Region Flexibility**: Support multiple AWS regions

### Environment Configuration

Use environment variables for configuration:

```python
import os

# Configuration with defaults
CONFIG = {
    "aws_region": os.getenv("AWS_REGION", "us-east-1"),
    "knowledge_base_id": os.getenv("KNOWLEDGE_BASE_ID"),
    "table_name": os.getenv("DYNAMODB_TABLE_NAME")
}
```

## Review Process

### Before Submitting

1. **Test Thoroughly**: Verify all functionality works as documented
2. **Check Dependencies**: Ensure all required packages are in requirements.txt
3. **Validate Metadata**: Confirm all metadata fields are accurate
4. **Cost Estimate**: Provide realistic cost estimates based on testing
5. **Documentation Review**: Have someone else review your documentation

### Pull Request Guidelines

1. **Clear Title**: Use descriptive PR titles
2. **Description**: Explain what the pattern does and why it's useful
3. **Testing Evidence**: Include screenshots or logs showing successful testing
4. **Breaking Changes**: Note any breaking changes or special requirements

### Review Criteria

Patterns are evaluated on:

- **Functionality**: Does it work as described?
- **Documentation**: Is it clear and complete?
- **Reusability**: Can others easily adapt it?
- **Code Quality**: Follows Python best practices?
- **Value**: Adds meaningful functionality to the repository?

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive in all interactions
- Focus on constructive feedback and improvements
- Help newcomers learn and contribute
- Acknowledge and credit others' work

### Getting Help

- **GitHub Discussions**: Ask questions and share ideas
- **Issues**: Report bugs or request features
- **Discord/Slack**: Join community channels for real-time help

## Pattern Categories

### Basic Agents
- Single agent with 1-2 tools
- Demonstrates core Strands functionality
- Beginner-friendly examples

### Multi-Agent Systems
- Agent orchestration patterns
- Swarm intelligence
- Hierarchical systems

### Knowledge & Retrieval
- RAG implementations
- Knowledge base integrations
- Information retrieval systems

### AWS Integrations
- Service-to-service patterns
- CloudFormation templates
- Serverless deployments

### Tool Integrations
- External API integrations
- Database connections
- Third-party services

### UI/UX Patterns
- Frontend integrations
- User interface patterns
- Deployment templates

Thank you for contributing to the Strands Agent Patterns community! 