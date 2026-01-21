# Lambda Performance Optimization and Error Prevention

## Memory and Timeout Errors

### Error: Task timed out after X seconds
**Root Cause**: Lambda execution exceeds configured timeout
**Common Scenarios**:
- Slow external API calls without timeout configuration
- Inefficient database queries
- Large file processing without streaming
- Cold start delays in VPC configurations

**Solutions**:
```python
# 1. Set explicit timeouts for external calls
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(total=3, backoff_factor=0.3)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

# Always set timeout
response = session.get(url, timeout=10)  # 10 second timeout

# 2. Use connection pooling for databases
import psycopg2.pool
connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10, **db_config)

# 3. Stream large files instead of loading into memory
import boto3
s3 = boto3.client('s3')
response = s3.get_object(Bucket='bucket', Key='large-file.csv')
for line in response['Body'].iter_lines():
    process_line(line)
```

**Prevention**:
- Set Lambda timeout to realistic value (not max 15 minutes by default)
- Monitor CloudWatch metrics: Duration, Throttles, Errors
- Use AWS X-Ray to identify slow operations
- Consider Step Functions for long-running workflows

### Error: Runtime exited with error: signal: killed
**Root Cause**: Lambda ran out of memory (OOM)
**Common Scenarios**:
- Loading large files entirely into memory
- Memory leaks in long-running functions
- Inefficient data structures
- Too many concurrent operations

**Solutions**:
```python
# 1. Process data in chunks
def process_large_file(file_path):
    chunk_size = 1024 * 1024  # 1MB chunks
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            process_chunk(chunk)

# 2. Use generators instead of lists
def get_records():
    # Bad - loads everything into memory
    return [process(item) for item in large_dataset]
    
    # Good - yields one at a time
    for item in large_dataset:
        yield process(item)

# 3. Clean up resources explicitly
import gc
large_object = process_data()
result = extract_result(large_object)
del large_object
gc.collect()  # Force garbage collection
```

**Prevention**:
- Monitor CloudWatch metric: MemoryUtilization
- Set memory to 1.5x-2x of typical usage
- Use memory profilers during development
- Consider Lambda layers to reduce deployment package size

## Cold Start Optimization

### Error: Slow first invocation (cold start)
**Root Cause**: Lambda initialization takes too long
**Common Scenarios**:
- Large deployment packages
- Heavy imports (pandas, numpy, ML libraries)
- VPC configuration overhead
- Database connection establishment

**Solutions**:
```python
# 1. Move imports inside functions (lazy loading)
def lambda_handler(event, context):
    # Only import when needed
    if event.get('use_ml'):
        import tensorflow as tf
        return ml_prediction(event)
    return simple_response(event)

# 2. Use Lambda layers for large dependencies
# Move heavy libraries to layers instead of deployment package

# 3. Keep connections warm (global scope)
import boto3
# Initialize outside handler - reused across invocations
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('my-table')

def lambda_handler(event, context):
    # Connection already established
    return table.get_item(Key={'id': event['id']})

# 4. Use Provisioned Concurrency for critical functions
# Configure via CDK/CloudFormation, not in code
```

**Prevention**:
- Keep deployment packages small (<50MB)
- Use Lambda layers for shared dependencies
- Enable Provisioned Concurrency for latency-sensitive functions
- Avoid VPC unless necessary (adds 10-15s cold start)
- Use Lambda SnapStart for Java functions

## Concurrency and Throttling

### Error: Rate exceeded / TooManyRequestsException
**Root Cause**: Lambda concurrency limit reached
**Common Scenarios**:
- Burst traffic without reserved concurrency
- Recursive invocations without limits
- Account-level concurrency limit (1000 default)
- Regional service quotas

**Solutions**:
```python
# 1. Implement exponential backoff for retries
import time
import random

def invoke_with_retry(lambda_client, function_name, payload, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = lambda_client.invoke(
                FunctionName=function_name,
                Payload=payload
            )
            return response
        except lambda_client.exceptions.TooManyRequestsException:
            if attempt == max_retries - 1:
                raise
            # Exponential backoff with jitter
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)

# 2. Use SQS for buffering
# Instead of direct Lambda invocation, send to SQS
# Lambda polls SQS with controlled concurrency
import boto3
sqs = boto3.client('sqs')
sqs.send_message(
    QueueUrl='queue-url',
    MessageBody=json.dumps(payload)
)

# 3. Set reserved concurrency to prevent runaway costs
# Configure in CDK/CloudFormation:
# reservedConcurrentExecutions: 100
```

**Prevention**:
- Set reserved concurrency for critical functions
- Use SQS for asynchronous processing
- Monitor CloudWatch metric: ConcurrentExecutions, Throttles
- Request service quota increases proactively
- Implement circuit breakers for downstream services

## Cost Optimization

### High Lambda Costs
**Root Cause**: Inefficient resource allocation or excessive invocations
**Common Scenarios**:
- Over-provisioned memory (paying for unused resources)
- Under-provisioned memory (longer duration, higher cost)
- Unnecessary invocations (polling instead of events)
- Not using ARM architecture (Graviton2)

**Solutions**:
```python
# 1. Right-size memory allocation
# Use AWS Lambda Power Tuning tool to find optimal memory
# https://github.com/alexcasalboni/aws-lambda-power-tuning

# 2. Use ARM architecture (20% cost savings)
# Configure in CDK:
# architecture: lambda.Architecture.ARM_64

# 3. Batch processing instead of individual invocations
def lambda_handler(event, context):
    # Process SQS batch (up to 10 messages)
    for record in event['Records']:
        process_message(record)
    # Single invocation for 10 messages vs 10 invocations

# 4. Use EventBridge Scheduler instead of CloudWatch Events
# More cost-effective for scheduled tasks
# Supports one-time schedules and flexible time windows
```

**Prevention**:
- Monitor CloudWatch metric: Duration, Invocations, Cost
- Use AWS Cost Explorer to track Lambda costs
- Set up billing alerts
- Review and optimize memory settings quarterly
- Consider Savings Plans for predictable workloads

## Error Handling Best Practices

### Proper Exception Handling
```python
import logging
from aws_lambda_powertools import Logger

logger = Logger()

def lambda_handler(event, context):
    try:
        # Business logic
        result = process_data(event)
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
    except ValueError as e:
        # Client error - don't retry
        logger.error(f"Validation error: {e}", exc_info=True)
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }
    except ConnectionError as e:
        # Transient error - can retry
        logger.error(f"Connection error: {e}", exc_info=True)
        raise  # Let Lambda retry
    except Exception as e:
        # Unexpected error - log and alert
        logger.exception(f"Unexpected error: {e}")
        # Send to monitoring/alerting
        raise

def process_data(event):
    # Validate input
    required_fields = ['user_id', 'action']
    missing = [f for f in required_fields if f not in event]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")
    
    # Process with proper error handling
    return perform_action(event)
```

## Monitoring and Observability

### Essential CloudWatch Metrics
- **Duration**: Execution time (optimize if consistently high)
- **Errors**: Failed invocations (investigate patterns)
- **Throttles**: Concurrency limit reached (increase limits or optimize)
- **IteratorAge**: For stream processing (indicates processing lag)
- **DeadLetterErrors**: Failed to send to DLQ (check DLQ configuration)

### Structured Logging
```python
from aws_lambda_powertools import Logger

logger = Logger()

@logger.inject_lambda_context
def lambda_handler(event, context):
    logger.info("Processing request", extra={
        "user_id": event.get("user_id"),
        "action": event.get("action"),
        "request_id": context.request_id
    })
    
    # Logs are structured JSON, easy to query in CloudWatch Insights
```

### CloudWatch Insights Queries
```
# Find errors by type
fields @timestamp, @message
| filter @message like /ERROR/
| stats count() by @message
| sort count desc

# Analyze cold starts
fields @timestamp, @duration, @initDuration
| filter @type = "REPORT"
| stats avg(@duration), avg(@initDuration), max(@duration)

# Memory utilization
fields @timestamp, @memorySize, @maxMemoryUsed
| filter @type = "REPORT"
| stats avg(@maxMemoryUsed / @memorySize * 100) as avg_memory_pct
```

## Quick Reference: Error to Solution Mapping

| Error Pattern | Likely Cause | First Action |
|--------------|--------------|--------------|
| Timeout | Slow external call | Add timeouts, check X-Ray trace |
| OOM (killed) | Memory leak | Increase memory, profile usage |
| Cold start >5s | Large package/VPC | Use layers, avoid VPC if possible |
| Throttling | High concurrency | Set reserved concurrency, use SQS |
| Connection refused | Network/security | Check security groups, VPC config |
| Access denied | IAM permissions | Review Lambda execution role |
| Module not found | Missing dependency | Check deployment package/layer |
| Syntax error | Code issue | Review recent changes, test locally |

## Additional Resources

- AWS Lambda Best Practices: https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html
- Lambda Power Tuning: https://github.com/alexcasalboni/aws-lambda-power-tuning
- AWS Lambda Powertools: https://awslabs.github.io/aws-lambda-powertools-python/
- AWS X-Ray: https://docs.aws.amazon.com/xray/latest/devguide/xray-services-lambda.html
