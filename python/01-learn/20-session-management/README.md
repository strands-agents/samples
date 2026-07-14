# Session Management

This tutorial demonstrates how to persist agent conversation state across restarts using the Strands Agents session management system. You'll progress from a stateless baseline to file-based, S3-based, and custom DynamoDB backends, then apply session persistence to multi-agent patterns.

## Tutorial Details

| Information            | Details                                                  |
|------------------------|----------------------------------------------------------|
| **Strands Features**   | `SessionManager`, `FileSessionManager`, `S3SessionManager`, `SessionRepository`, `Swarm`, `Graph` |
| **Agent Pattern**      | Single agent, Swarm, Graph                               |
| **Tools**              | None                                                     |
| **Model**              | Default Bedrock model                                    |

## Key Concepts

- **SessionManager**: Abstract interface that hooks into agent lifecycle events to persist conversation state automatically
- **FileSessionManager**: Built-in backend that stores sessions as JSON files on the local filesystem
- **S3SessionManager**: Built-in backend that stores sessions in an S3 bucket for cloud-based persistence
- **SessionRepository**: Abstract interface for implementing custom storage backends (e.g., DynamoDB)
- **Multi-agent sessions**: Session persistence applied to Swarm and Graph orchestration patterns

## Prerequisites

- Python 3.10 or higher
- AWS account with Amazon Bedrock model access
- Model access enabled in Amazon Bedrock
- AWS credentials configured (for the S3 and DynamoDB sections)

## AWS Credentials Setup

Both notebooks include an optional setup cell at the top for configuring credentials.
By default the notebooks use the standard boto3 credential chain (environment variables,
`~/.aws/credentials`, IAM role, etc.).

If you use a named AWS profile, uncomment and set the profile name in the setup cell:

```python
# os.environ["AWS_PROFILE"] = "your-profile-name"
```

The region and account ID are derived automatically from your active credentials:

```python
REGION = boto3.session.Session().region_name or "us-east-1"
ACCOUNT_ID = boto3.client("sts").get_caller_identity()["Account"]
```

For SageMaker notebook instances or environments with an attached IAM role, no
credential configuration is needed — the role is picked up automatically.

## Tutorial Structure

| Notebook | Description |
|----------|-------------|
| [01-single-agent-persistence.ipynb](./01-single-agent-persistence.ipynb) | Baseline failure → FileSessionManager → S3 backend → custom DynamoDB backend |
| [02-multi-agent-persistence.ipynb](./02-multi-agent-persistence.ipynb) | Session persistence with Swarm and Graph patterns |

### Notebook 1 walkthrough

1. **Baseline** — see an agent lose memory on restart (a few cells)
2. **FileSessionManager** — persist to the local filesystem, inspect the files, restore
3. **S3SessionManager** — swap the backend constructor, everything else stays the same
4. **DynamoDB** (advanced) — implement `SessionRepository` for a custom single-table design

### Notebook 2 walkthrough

1. **Swarm** — two collaborating agents with `S3SessionManager` on the orchestrator
2. **Graph** — deterministic three-node pipeline with `FileSessionManager` on the orchestrator

## Getting Started

### Option A: Local Machine

1. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Jupyter (if not already installed):**
   ```bash
   pip install jupyter
   ```

4. **Launch the notebooks:**
   ```bash
   jupyter notebook
   ```

### Option B: SageMaker Notebook Instance

1. **Open a terminal** in your SageMaker notebook instance.

2. **Clone the repository** (if not already done):
   ```bash
   git clone https://github.com/strands-agents/samples.git
   cd samples/python/01-learn/20-session-management
   ```

3. **Install dependencies** in the first cell of each notebook (already included):
   ```python
   %pip install -q --upgrade strands-agents boto3
   ```

4. **Open the notebooks** from the Jupyter file browser and run them in order.

## Project Structure

```
20-session-management/
├── README.md
├── requirements.txt
├── 01-single-agent-persistence.ipynb
└── 02-multi-agent-persistence.ipynb
```

## Cleanup

- **FileSessionManager**: Delete the `sessions/` folder created during the notebook run.
- **S3SessionManager** (notebook 01): The cleanup cell deletes the session objects and bucket.
- **S3SessionManager** (notebook 02 Swarm): The cleanup cell deletes the swarm session bucket.
- **DynamoDB**: The cleanup cell in notebook 01 deletes the DynamoDB table.

## Additional Resources

- [Strands Agents Documentation](https://strandsagents.com/)
- [SessionManager API Reference](https://strandsagents.com/docs/api/python/strands.session.session_manager/)
- [FileSessionManager API Reference](https://strandsagents.com/docs/api/python/strands.session.file_session_manager/)
- [S3SessionManager API Reference](https://strandsagents.com/docs/api/python/strands.session.s3_session_manager/)
- [SessionRepository API Reference](https://strandsagents.com/docs/api/python/strands.session.session_repository/)
