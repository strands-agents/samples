# Tutorial README Template

Use this template when creating a new tutorial in `01-tutorials/`.

## Guidelines

- Refer to [`structure.md`](./structure.md) for choosing the appropriate project structure
- Focus on educational content and concept explanation
- Be concise but thorough—tutorials should teach, not just demonstrate
- Test all commands before documenting
- Use code blocks for all terminal commands
- Add optional sections as needed (see below)

---

# [Tutorial Title]

[1-2 sentence description of what this tutorial demonstrates and why it's useful.]

![Architecture Diagram](./images/architecture.png)

## Tutorial Details

| Information            | Details                                                  |
|------------------------|----------------------------------------------------------|
| **Strands Features**   | [Multi-agent orchestration, A2A protocol, MCP tool integration, ...] |
| **Agent Pattern**      | [Single agent / Orchestrator + specialist agents / Swarm / Graph] |
| **Tools**              | [Custom tools, MCP tools, A2A client tools, or "None"]   |
| **Model**              | [Claude Sonnet 4 on Amazon Bedrock / ...]                |

## Key Concepts

- **[Concept 1]**: Brief explanation of the concept
- **[Concept 2]**: Brief explanation of the concept
- **[Concept 3]**: Brief explanation of the concept

## Prerequisites

- Python 3.10 or higher
- AWS account with Amazon Bedrock model access
- [Model name] model access in Amazon Bedrock (`[model-id]`)
- [Additional requirements specific to this tutorial]

## Tutorial Structure

| Notebook | Description |
|----------|-------------|
| [01-notebook-name.ipynb](./01-notebook-name.ipynb) | [What this notebook covers] |
| [02-notebook-name.ipynb](./02-notebook-name.ipynb) | [What this notebook covers] |

## Getting Started

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the notebooks in order:**
   - **Notebook 1**: [What it does]
   - **Notebook 2**: [What it does]

3. **Test the system** [how to verify everything works]:
   - [Example query or test]
   - [Example query or test]

## Project Structure

```
[tutorial-folder]/
├── 01-notebook-name.ipynb
├── 02-notebook-name.ipynb
├── requirements.txt
├── [agent_folder]/
│   ├── [main_file].py
│   └── requirements.txt
└── utils/
    └── [helper].py
```

## Cleanup

[Explain how to clean up any AWS resources created by the tutorial.]

## Additional Resources

- [Strands Agents Documentation](https://strandsagents.com/)
- [Related Tutorial](../path-to-related-tutorial/)
- [AWS Documentation](https://docs.aws.amazon.com/)

---

## Common Optional Sections

Based on analysis of existing tutorials, consider adding these sections as appropriate:

### Best Practices
```markdown
## Best Practices

- [Practice 1]
- [Practice 2]
```

### Experiment Ideas
```markdown
## Experiment Ideas

- [Idea 1: Suggestion for extending the tutorial]
- [Idea 2: Alternative approach to try]
```

### Flow Overview
For multi-agent tutorials, show step-by-step collaboration:
```markdown
## Flow Overview
1. User → Agent A
2. Agent A → Agent B
3. Agent B → Final output
```

### Troubleshooting
Common issues and solutions:
```markdown
## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| [Issue] | [Cause]     | [Solution] |
```

### Code Walkthrough
For complex tutorials, explain key code sections:
```markdown
## Code Walkthrough
### Agent Configuration
[Explanation of important code blocks]
```

