# README Template Instructions

When creating a new sample in the `02-samples` folder, follow this structure to ensure consistency and clarity.

A sample README must include:
- A descriptive title
- An overview section with sample details and architecture
- Prerequisites
- Setup instructions
- Usage/execution instructions
- Cleanup instructions (if infrastructure is required)

## Guidelines

- Refer to [`structure.md`](./structure.md) for choosing the appropriate project structure
- Be concise and actionable
- Focus on actionable steps for users rather than lengthy explanations
- Commands are illustrative—adapt them to your implementation. Structure matters most.
- Test all commands before documenting
- Use code blocks for all terminal commands
- Adapt complexity based on your sample type
- Add optional sections as needed based on your sample's requirements (see below)

---

# [Sample Title]

[Brief 1-2 sentence description of what this sample demonstrates]

## Overview

### Sample Details

| Information            | Details                                                    |
|------------------------|------------------------------------------------------------|
| **Agent Architecture** | [Single-agent / Multi-agent / Swarm]                       |
| **Native Tools**       | [List native Strands tools, or "None"]                     |
| **Custom Tools**       | [List custom tools, or "None"]                             |
| **MCP Servers**        | [List MCP servers used, or "None"]                         |
| **Use Case Vertical**  | [Industry/domain: Finance, Healthcare, Retail, etc.]       |
| **Complexity**         | [Basic / Intermediate / Advanced]                          |
| **Model Provider**     | [Amazon Bedrock / Other]                                   |
| **SDK Used**           | [Strands Agents SDK / boto3 / AWS CDK / Other]             |

### Architecture

![Architecture Diagram](./images/architecture.png)

[Optional: Brief description of the architecture and how components interact]

### Key Features

- [Feature 1: What makes this sample unique]
- [Feature 2: Important capability demonstrated]
- [Feature 3: Notable pattern or technique]

## Prerequisites

- Python **3.10+**
- [uv](https://docs.astral.sh/uv/getting-started/installation/) for dependency management
- AWS CLI configured with appropriate credentials
- [Model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html) enabled for [specific models]
- [Any additional service-specific requirements]

## Setup

1. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **[Optional] Deploy infrastructure** (if required):
   ```bash
   cd infrastructure
   ./deploy_prereqs.sh
   ```

## Usage

**Run the sample:**
```bash
uv run [main_file].py
```

**[Optional] With arguments:**
```bash
uv run [main_file].py --option value
```

**[Optional] CLI commands** (if applicable):
```bash
# Example command
uv run [main_file].py command "argument"
```

## Cleanup

[If infrastructure setup was required]

```bash
cd infrastructure
./cleanup.sh
```

## Common Optional Sections

Based on analysis of existing samples, consider adding these sections as appropriate for your use case:

### Example Queries/Interactions
Help users understand what they can do:
```markdown
## Example Queries
- "Example interaction 1"
- "Example interaction 2"
```

### Flow Overview
For multi-agent systems, show step-by-step collaboration:
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

### Project Structure
For complex samples with many components:
```markdown
## Project Structure

| Component | File(s) | Description |
|-----------|---------|-------------|
| [Name]    | [Path]  | [Purpose]   |
```

### Additional Resources
External documentation and learning materials:
```markdown
## Additional Resources
- [Link to relevant documentation]
- [Related tutorials or guides]
```

---

## Disclaimer

This sample is provided for educational and demonstration purposes only. It is not intended for production use without further development, testing, and hardening.

For production deployments, consider:
- Implementing appropriate content filtering and safety measures
- Following security best practices for your deployment environment
- Conducting thorough testing and validation
- Reviewing and adjusting configurations for your specific requirements
