# Lambda Development Best Practices

## Error Handling

### Use Specific Exception Types

```python
# Good - Catch specific exceptions for better error handling
try:
    result = process_data(input_data)
except ValueError as e:
    logger.error(f"Invalid input data: {e}")
    return {"statusCode": 400, "error": "Invalid input"}
except ConnectionError as e:
    logger.error(f"Network error: {e}")
    return {"statusCode": 503, "error": "Service unavailable"}
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return {"statusCode": 500, "error": "Internal error"}
```

### Implement Retry Logic

```python
from retrying import retry

@retry(
    wait_exponential_multiplier=1000,
    wait_exponential_max=10000,
    stop_max_attempt_number=3,
    retry_on_exception=lambda x: isinstance(x, (ConnectionError, TimeoutError))
)
def call_external_api():
    # API call implementation
    pass
```

## Logging Best Practices

### Structured Logging

```python
from aws_lambda_powertools import Logger

logger = Logger()

# Good - structured logging with context
logger.info("Processing task", extra={
    "task_id": task_id,
    "operation": "data_processing",
    "user_id": user_id
})

# Include comprehensive error context
logger.error("Task failed", extra={
    "task_id": task_id,
    "error_type": type(e).__name__,
    "error_message": str(e),
    "stack_trace": traceback.format_exc(),
    "request_id": context.aws_request_id
})
```

## Input Validation

### Validate Early and Often

```python
def process_task(event):
    # Validate required fields
    required_fields = ['taskId', 'userId', 'action']
    for field in required_fields:
        if field not in event:
            raise ValueError(f"Missing required field: {field}")

    # Validate data types
    if not isinstance(event['taskId'], int):
        raise TypeError(f"taskId must be integer, got {type(event['taskId'])}")

    # Validate ranges and constraints
    if event['taskId'] <= 0:
        raise ValueError(f"taskId must be positive, got {event['taskId']}")

    # Validate enum values
    valid_actions = ['create', 'update', 'delete']
    if event['action'] not in valid_actions:
        raise ValueError(f"Invalid action: {event['action']}")
```

## Performance Optimization

### Connection Pooling

```python
import boto3
from botocore.config import Config

# Configure connection pooling
config = Config(
    max_pool_connections=50,
    retries={'max_attempts': 3}
)

# Reuse clients
dynamodb = boto3.resource('dynamodb', config=config)
ec2 = boto3.client('ec2', config=config)
```

### Batch Operations

```python
# Good - batch DynamoDB operations
with dynamodb.batch_writer() as batch:
    for item in items:
        batch.put_item(Item=item)

# Good - batch processing for large datasets
def process_in_batches(items, batch_size=25):
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        process_batch(batch)
```

## Security Best Practices

### Use IAM Roles and Policies (Least Privilege)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:Query"],
      "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/MyTable"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::my-bucket/*"
    }
  ]
}
```

### Secrets Management

```python
import boto3

def get_secret(secret_name):
    secrets_client = boto3.client('secretsmanager')
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        logger.error(f"Failed to retrieve secret {secret_name}: {e}")
        raise
```

## Testing Strategies

### Unit Testing

```python
import unittest
from unittest.mock import patch, MagicMock

class TestLambdaFunction(unittest.TestCase):

    @patch('boto3.client')
    def test_process_task_success(self, mock_boto3):
        # Mock AWS services
        mock_dynamodb = MagicMock()
        mock_boto3.return_value = mock_dynamodb

        # Test successful processing
        event = {'taskId': 123, 'action': 'create'}
        result = process_task(event)

        self.assertEqual(result['status'], 'success')
        mock_dynamodb.put_item.assert_called_once()

    def test_invalid_input_raises_error(self):
        # Test error handling
        event = {'taskId': -1}  # Invalid
        with self.assertRaises(ValueError):
            process_task(event)
```

## Monitoring and Observability

### CloudWatch Metrics

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def publish_custom_metric(metric_name, value, unit='Count'):
    cloudwatch.put_metric_data(
        Namespace='LambdaErrorAnalysis',
        MetricData=[
            {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Dimensions': [
                    {
                        'Name': 'Environment',
                        'Value': os.environ.get('ENVIRONMENT', 'dev')
                    }
                ]
            }
        ]
    )
```

## Documentation Standards

### Function Documentation

```python
def process_user_data(
    user_id: str,
    data: Dict[str, Any],
    options: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Process user data and store in DynamoDB.

    Args:
        user_id: Unique user identifier
        data: User data dictionary to process
        options: Optional processing configuration

    Returns:
        Dictionary containing processing result and metadata

    Raises:
        ValueError: If user_id or data is invalid
        ConnectionError: If AWS API calls fail

    Example:
        >>> result = process_user_data('user123', {'name': 'John'})
        >>> print(result['status'])
        'success'
    """
    pass
```

## Lambda-Specific Best Practices

### Environment Variables

```python
import os

# Always provide defaults for optional config
TIMEOUT = int(os.environ.get('TIMEOUT', '30'))
BATCH_SIZE = int(os.environ.get('BATCH_SIZE', '25'))
ENABLE_DEBUG = os.environ.get('ENABLE_DEBUG', 'false').lower() == 'true'

# Validate required environment variables at startup
REQUIRED_VARS = ['TABLE_NAME', 'BUCKET_NAME']
for var in REQUIRED_VARS:
    if var not in os.environ:
        raise ValueError(f"Missing required environment variable: {var}")
```

### Cold Start Optimization

```python
# Initialize clients outside handler for reuse
import boto3

# These are initialized once per container
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    # Handler code reuses initialized clients
    table.put_item(Item={'id': '123'})
```

### Memory and Timeout Configuration

- Start with 512MB memory and adjust based on CloudWatch metrics
- Set timeout to 3x expected execution time
- Monitor memory usage and adjust accordingly
- Use provisioned concurrency for latency-sensitive functions
