# Tutorial README Template

Use this template when creating a new tutorial in `01-tutorials/`.

## Guidelines

- Refer to [`structure.md`](./structure.md) for choosing the appropriate project structure
- Focus on educational content and concept explanation
- Be concise but thorough—tutorials should teach, not just demonstrate
- Test all commands before documenting
- Use code blocks for all terminal commands
- Adapt complexity based on your tutorial's learning objectives
- Add optional sections as needed (see below)

---

# [Tutorial Title]

[1-2 sentence description of what this tutorial demonstrates and why it's useful.]

## Overview

### Tutorial Details

| Information            | Details                                                  |
|------------------------|----------------------------------------------------------|
| **Strands Feature**    | [Agent / Tools / Memory / Streaming / Multi-agent / MCP] |
| **Agent Pattern**      | [Single-agent / Multi-agent / Swarm / Graph]             |
| **Tools Used**         | [Native tools, custom tools, or "None"]                  |
| **Complexity**         | [Beginner / Intermediate / Advanced]                     |
| **Model Provider**     | [Amazon Bedrock / Anthropic / OpenAI / Ollama]           |

### Key Concepts

- **[Concept 1]**: Brief explanation of the concept
- **[Concept 2]**: Brief explanation of the concept
- **[Concept 3]**: Brief explanation of the concept

### Architecture

![Architecture Diagram](./images/architecture.png)

[Brief description of the architecture diagram and how components interact.]

## Prerequisites

- Python **3.10+**
- AWS account with Amazon Bedrock model access
- [Additional requirements specific to this tutorial]

### Model Access

This tutorial uses the following models:
- `[model-id]` - [Purpose]

## Getting Started

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the notebook:**
   ```
   [tutorial-name].ipynb
   ```

## Execution Instructions

### Step 1: [First Step]

```bash
[command]
```

This command:
- [What it does]
- [Expected outcome]

### Step 2: [Second Step]

```bash
[command]
```

[Explanation of what happens.]

## [Feature-Specific Section] (Optional)

[For complex tutorials, include tables or code blocks explaining key mechanisms.]

| Parameter | Description | Default |
|-----------|-------------|---------|
| `param1` | Description | `value` |
| `param2` | Description | `value` |

## Best Practices

- [Practice 1]
- [Practice 2]
- [Practice 3]

## Cleanup (If Applicable)

If you created any AWS resources, clean them up:

```bash
cd infrastructure
./cleanup.sh
```

## Experiment Ideas

- [Idea 1: Suggestion for extending the tutorial]
- [Idea 2: Alternative approach to try]

## Resources

- [Strands Agents Documentation](https://strandsagents.com/)
- [Related Tutorial](../path-to-related-tutorial/)
- [AWS Documentation](https://docs.aws.amazon.com/)

## Common Optional Sections

Based on analysis of existing tutorials, consider adding these sections as appropriate:

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

---

## Disclaimer

This tutorial is provided for educational and demonstration purposes only. It is not intended for production use without further development, testing, and hardening.

For production deployments, consider:
- Implementing appropriate content filtering and safety measures
- Following security best practices for your deployment environment
- Conducting thorough testing and validation
- Reviewing and adjusting configurations for your specific requirements
