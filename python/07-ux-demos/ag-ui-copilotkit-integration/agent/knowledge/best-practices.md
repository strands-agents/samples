# AgentCore Best Practices

Follow these best practices to build robust, scalable AI agents on AgentCore.

## Architecture Best Practices

### 1. Design for Statelessness

While AgentCore Memory provides persistence, design your agent to be stateless:

```python
# Good: Retrieve state from memory each request
@tool
def get_user_preferences(user_id: str) -> dict:
    return memory.retrieve(f"/preferences/{user_id}")

# Avoid: Storing state in global variables
user_prefs = {}  # Don't do this!
```

### 2. Use Appropriate Model Sizes

Choose the right model for your use case. On Amazon Bedrock, the current Anthropic Claude family:

| Model | Best For |
|-------|----------|
| **Claude Haiku 4.5** | Simple tasks, high volume, latency-sensitive paths |
| **Claude Sonnet 4.6** | Balanced default for coding, tool use, long-context reasoning, agent planning |
| **Claude Opus 4.6** | Most complex reasoning, long-horizon agentic tasks, large codebases |

Prefer a cross-region inference profile ID (e.g. `us.anthropic.claude-sonnet-4-6`) over an in-region model ID for higher throughput.

### 3. Implement Graceful Degradation

Handle tool failures gracefully:

```python
@tool
def search_database(query: str) -> str:
    try:
        results = db.search(query)
        return json.dumps(results)
    except DatabaseError:
        return "Database temporarily unavailable. Please try again."
```

## Security Best Practices

### 1. Validate All Inputs

Never trust user input:

```python
@tool
def process_file(filename: str) -> str:
    # Validate filename
    if ".." in filename or filename.startswith("/"):
        return "Invalid filename"
    
    safe_path = ALLOWED_DIR / filename
    # ... process file
```

### 2. Use IAM Roles

Configure minimal IAM permissions:

```yaml
# Good: Specific permissions
- Effect: Allow
  Action:
    - bedrock:InvokeModel
  Resource:
    - arn:aws:bedrock:*:*:model/anthropic.claude-sonnet-4-6
    - arn:aws:bedrock:*:*:inference-profile/us.anthropic.claude-sonnet-4-6

# Avoid: Wildcard permissions
- Effect: Allow
  Action: "*"
  Resource: "*"
```

### 3. Protect Sensitive Data

Never log or expose sensitive information:

```python
# Good: Mask sensitive data
logger.info(f"Processing request for user {user_id[:4]}***")

# Avoid: Logging full credentials
logger.info(f"API key: {api_key}")  # Never do this!
```

## Performance Best Practices

### 1. Optimize Cold Starts

Minimize initialization time:

```python
# Good: Lazy loading
_client = None

def get_client():
    global _client
    if _client is None:
        _client = boto3.client('bedrock-runtime')
    return _client

# Avoid: Loading at import time
client = boto3.client('bedrock-runtime')  # Slows cold start
```

### 2. Use Streaming

Enable streaming for better UX:

```python
# AG-UI automatically handles streaming
# Just ensure your agent supports it
agui_agent = StrandsAgent(
    agent=agent,
    name="my_agent",
)
```

### 3. Cache When Appropriate

Cache expensive operations:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_static_content(key: str) -> str:
    return s3.get_object(Bucket=BUCKET, Key=key)['Body'].read()
```

## Observability Best Practices

### 1. Structured Logging

Use structured logs for easier analysis:

```python
import json
import logging

logger = logging.getLogger(__name__)

def log_event(event_type: str, **kwargs):
    logger.info(json.dumps({
        "event": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs
    }))
```

### 2. Track Key Metrics

Monitor these metrics:

- **Latency** - Response time per request
- **Error rate** - Failed requests percentage
- **Token usage** - Input/output tokens per request
- **Tool calls** - Frequency and duration of tool usage

### 3. Set Up Alerts

Configure CloudWatch alarms for:

- Error rate > 5%
- P99 latency > 10s
- Memory usage > 80%

## Testing Best Practices

### 1. Test Locally First

Always test before deploying:

```bash
# Run agent locally
python main.py

# Test with curl
curl -X POST http://localhost:8001 \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

### 2. Use Integration Tests

Test the full flow:

```python
def test_agent_with_tools():
    response = agent("Search for AgentCore documentation")
    assert "search_knowledge" in response.tool_calls
    assert len(response.content) > 0
```

### 3. Load Test Before Production

Use tools like Locust or k6 to simulate traffic:

```python
# locustfile.py
from locust import HttpUser, task

class AgentUser(HttpUser):
    @task
    def chat(self):
        self.client.post("/", json={"message": "Hello"})
```
