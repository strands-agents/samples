# AWS Service Error Codes and Solutions

## Lambda Service Errors

### Runtime Errors

#### `Runtime.ImportModuleError`
**Cause**: Missing Python module or incorrect import path
**Solutions**:
- Verify module is included in deployment package
- Check import path and module name spelling
- Ensure dependencies are in Lambda layer or package
- Use `pip install -t` for local dependencies
- Check Python version compatibility

#### `Runtime.HandlerNotFound`
**Cause**: Lambda handler function not found
**Solutions**:
- Verify handler configuration matches function name
- Check file name and function name spelling
- Ensure handler file is in root of deployment package
- Verify function signature matches expected format
- Check for typos in handler path

#### `Runtime.ExitError`
**Cause**: Function process exited unexpectedly
**Solutions**:
- Check for unhandled exceptions
- Review memory usage and allocation
- Verify timeout settings
- Add proper error handling
- Check for system-level errors

#### `Runtime.Unknown`
**Cause**: Unexpected runtime error
**Solutions**:
- Check CloudWatch logs for details
- Verify runtime version compatibility
- Review recent code changes
- Test with simplified code
- Contact AWS support if persistent

### Resource Errors

#### `ResourceConflictException`
**Cause**: Resource is being modified by another operation
**Solutions**:
- Wait and retry the operation
- Check for concurrent modifications
- Implement proper locking mechanisms
- Use eventual consistency patterns
- Add exponential backoff

#### `ResourceNotFoundException`
**Cause**: Referenced resource does not exist
**Solutions**:
- Verify resource ARN or name
- Check resource region and account
- Ensure resource has been created
- Verify permissions to access resource
- Check for typos in resource identifiers

#### `InvalidParameterValueException`
**Cause**: Invalid parameter value provided
**Solutions**:
- Validate parameter formats
- Check parameter value ranges
- Review API documentation
- Verify data types
- Test with known good values

## IAM and Security Errors

### Permission Errors

#### `AccessDenied`
**Cause**: Insufficient permissions for requested action
**Solutions**:
- Add required permissions to IAM role
- Check resource-based policies
- Verify cross-account trust relationships
- Review condition statements in policies
- Use IAM policy simulator to test

#### `UnauthorizedOperation`
**Cause**: Action not allowed by current permissions
**Solutions**:
- Grant specific action permissions
- Check service-specific permissions
- Verify resource ARN patterns
- Review policy evaluation logic
- Check for explicit deny statements

#### `InvalidUserID.NotFound`
**Cause**: IAM user or role does not exist
**Solutions**:
- Verify user/role ARN spelling
- Check account ID in ARN
- Ensure user/role exists in correct account
- Verify cross-account role assumptions
- Check for deleted resources

### Authentication Errors

#### `SignatureDoesNotMatch`
**Cause**: AWS signature calculation error
**Solutions**:
- Check AWS credentials configuration
- Verify system clock synchronization
- Update AWS SDK to latest version
- Review credential provider chain
- Check for special characters in credentials

#### `TokenRefreshRequired`
**Cause**: Temporary credentials have expired
**Solutions**:
- Refresh STS tokens
- Check token expiration time
- Implement automatic token refresh
- Use IAM roles instead of temporary credentials
- Increase token duration if possible

#### `ExpiredToken`
**Cause**: Security token has expired
**Solutions**:
- Obtain new credentials
- Implement credential refresh logic
- Use IAM roles for automatic rotation
- Check credential expiration times
- Monitor credential age

## S3 Service Errors

### Access Errors

#### `NoSuchBucket`
**Cause**: S3 bucket does not exist or wrong region
**Solutions**:
- Verify bucket name spelling
- Check bucket region configuration
- Ensure bucket exists in correct account
- Verify cross-region access patterns
- Check for bucket deletion

#### `NoSuchKey`
**Cause**: S3 object key does not exist
**Solutions**:
- Verify object key path
- Check for case sensitivity
- Ensure object has been uploaded
- Verify object versioning settings
- Check for object deletion

#### `AccessDenied` (S3)
**Cause**: Insufficient S3 permissions
**Solutions**:
- Add S3 permissions to IAM role
- Check bucket policies
- Verify object ACLs
- Review cross-account bucket access
- Check for bucket encryption requirements

### Configuration Errors

#### `InvalidBucketName`
**Cause**: Bucket name violates naming rules
**Solutions**:
- Use lowercase letters, numbers, hyphens
- Avoid periods in bucket names
- Ensure name is globally unique
- Follow S3 naming conventions
- Check name length (3-63 characters)

#### `BucketAlreadyExists`
**Cause**: Bucket name already taken globally
**Solutions**:
- Choose a different bucket name
- Add unique prefix or suffix
- Use account ID in bucket name
- Check for naming conflicts
- Verify bucket ownership

## DynamoDB Service Errors

### Capacity Errors

#### `ProvisionedThroughputExceededException`
**Cause**: Request rate exceeds provisioned capacity
**Solutions**:
- Increase provisioned read/write capacity
- Implement exponential backoff retry
- Use DynamoDB auto-scaling
- Consider on-demand billing mode
- Optimize query patterns

#### `ThrottlingException`
**Cause**: Request rate too high for current capacity
**Solutions**:
- Implement retry with jitter
- Distribute requests across partition keys
- Use batch operations efficiently
- Monitor and adjust capacity settings
- Consider caching frequently accessed data

#### `RequestLimitExceeded`
**Cause**: Too many requests in short time
**Solutions**:
- Implement rate limiting
- Add exponential backoff
- Distribute load over time
- Use batch operations
- Monitor request patterns

### Data Errors

#### `ValidationException`
**Cause**: Invalid request parameters or data
**Solutions**:
- Validate input data format
- Check attribute names and types
- Verify key schema requirements
- Review DynamoDB data type constraints
- Test with sample data

#### `ConditionalCheckFailedException`
**Cause**: Conditional expression evaluated to false
**Solutions**:
- Review conditional expression logic
- Check item state before update
- Implement proper concurrency control
- Use optimistic locking patterns
- Add retry logic for conflicts

#### `ItemCollectionSizeLimitExceededException`
**Cause**: Item collection exceeds 10GB limit
**Solutions**:
- Redesign partition key strategy
- Distribute data across partitions
- Archive old data
- Use composite keys
- Consider table redesign

## EventBridge Service Errors

### Rule Errors

#### `ResourceNotFoundException` (EventBridge)
**Cause**: Event rule or bus does not exist
**Solutions**:
- Verify rule name and event bus
- Check rule region and account
- Ensure rule has been created
- Verify cross-account permissions
- Check for rule deletion

#### `LimitExceededException`
**Cause**: Service limits exceeded
**Solutions**:
- Review EventBridge service limits
- Optimize event patterns
- Use multiple event buses
- Request limit increases if needed
- Consolidate similar rules

### Event Processing Errors

#### `InvalidEventPatternException`
**Cause**: Event pattern syntax is invalid
**Solutions**:
- Validate event pattern JSON syntax
- Check pattern matching rules
- Test patterns with sample events
- Review EventBridge pattern documentation
- Use pattern testing tools

#### `ManagedRuleException`
**Cause**: Error in managed rule execution
**Solutions**:
- Check rule configuration
- Verify target permissions
- Review CloudWatch logs
- Test rule with sample events
- Check target availability

## Bedrock Service Errors

### Model Errors

#### `ValidationException` (Bedrock)
**Cause**: Invalid model parameters or input
**Solutions**:
- Validate input text length and format
- Check model parameter ranges
- Verify model ID and availability
- Review model-specific requirements
- Test with smaller inputs

#### `ThrottlingException` (Bedrock)
**Cause**: Request rate exceeds model limits
**Solutions**:
- Implement exponential backoff
- Distribute requests over time
- Use multiple model endpoints
- Consider provisioned throughput
- Monitor request rates

#### `ModelNotReadyException`
**Cause**: Model is not available or loading
**Solutions**:
- Wait for model to become ready
- Check model status and region
- Verify model provisioning
- Implement retry logic with delays
- Use alternative models

#### `ModelTimeoutException`
**Cause**: Model inference timed out
**Solutions**:
- Reduce input size
- Simplify prompts
- Increase timeout settings
- Use streaming responses
- Consider model alternatives

### Knowledge Base Errors

#### `ResourceNotFoundException` (Knowledge Base)
**Cause**: Knowledge base does not exist
**Solutions**:
- Verify knowledge base ID
- Check knowledge base region
- Ensure knowledge base is created
- Verify access permissions
- Check for deletion

#### `AccessDeniedException` (Knowledge Base)
**Cause**: Insufficient permissions for knowledge base
**Solutions**:
- Add Bedrock permissions to IAM role
- Verify knowledge base resource policies
- Check cross-account access settings
- Review service-linked role permissions
- Test with IAM policy simulator

## CloudWatch Service Errors

### Logs Errors

#### `ResourceNotFoundException` (CloudWatch Logs)
**Cause**: Log group or stream does not exist
**Solutions**:
- Verify log group name
- Check log stream existence
- Ensure logs are being generated
- Verify log retention settings
- Check for log group deletion

#### `InvalidParameterException`
**Cause**: Invalid CloudWatch Logs API parameters
**Solutions**:
- Validate parameter formats
- Check timestamp ranges
- Verify filter patterns
- Review API parameter requirements
- Test with known good values

#### `DataAlreadyAcceptedException`
**Cause**: Log events already accepted
**Solutions**:
- Check for duplicate submissions
- Verify sequence tokens
- Implement idempotency
- Review log submission logic
- Use unique request IDs

### Metrics Errors

#### `InvalidParameterValue`
**Cause**: Invalid metric parameter values
**Solutions**:
- Validate metric names and dimensions
- Check timestamp formats
- Verify metric value ranges
- Review CloudWatch naming conventions
- Test with sample data

## General Error Handling Patterns

### Retry Strategies

#### Exponential Backoff
```python
import time
import random

def exponential_backoff_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
```

#### Exponential Backoff with Jitter
```python
import time
import random

def retry_with_jitter(func, max_retries=5, base_delay=1, max_delay=32):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            # Full jitter strategy
            delay = min(max_delay, base_delay * (2 ** attempt))
            jittered_delay = random.uniform(0, delay)
            time.sleep(jittered_delay)
```

#### Circuit Breaker Pattern
```python
import time

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func()
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e
    
    def on_success(self):
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
```

### Error Classification

#### Transient Errors (Retry Recommended)
- Network timeouts
- Service throttling
- Temporary service unavailability
- Rate limiting
- Connection resets
- 429, 500, 502, 503, 504 HTTP errors

#### Permanent Errors (Don't Retry)
- Authentication failures (401, 403)
- Invalid parameters (400)
- Resource not found (404)
- Permission denied
- Invalid request format
- Malformed data

#### Unknown Errors (Limited Retry)
- Unexpected service errors
- Unknown error codes
- Service internal errors
- Unhandled exceptions

### Error Response Handling

```python
def handle_aws_error(error):
    """Classify and handle AWS errors appropriately"""
    error_code = error.response.get('Error', {}).get('Code', 'Unknown')
    
    # Transient errors - retry
    transient_errors = [
        'ThrottlingException',
        'ProvisionedThroughputExceededException',
        'RequestLimitExceeded',
        'ServiceUnavailable',
        'InternalError'
    ]
    
    # Permanent errors - don't retry
    permanent_errors = [
        'AccessDenied',
        'InvalidParameterValue',
        'ResourceNotFoundException',
        'ValidationException'
    ]
    
    if error_code in transient_errors:
        return 'RETRY'
    elif error_code in permanent_errors:
        return 'FAIL'
    else:
        return 'RETRY_LIMITED'
```

## Service-Specific Best Practices

### Lambda
- Use appropriate timeout and memory settings
- Implement proper error handling
- Monitor CloudWatch metrics
- Use X-Ray for tracing
- Test with various input scenarios

### DynamoDB
- Design for even partition key distribution
- Use batch operations when possible
- Implement exponential backoff
- Monitor capacity metrics
- Use on-demand for unpredictable workloads

### S3
- Handle eventual consistency
- Use appropriate storage classes
- Implement lifecycle policies
- Monitor access patterns
- Use versioning for critical data

### Bedrock
- Validate input before API calls
- Implement proper retry logic
- Monitor token usage
- Cache responses when appropriate
- Handle model-specific errors

### EventBridge
- Design efficient event patterns
- Monitor rule execution
- Use dead letter queues
- Test patterns thoroughly
- Implement proper error handling in targets
