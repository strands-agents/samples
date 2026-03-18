# Common Lambda Errors and Solutions

## Python Runtime Errors

### ValueError: invalid literal for int()
**Cause**: Attempting to convert a non-numeric string to an integer
**Solution**: Add input validation before conversion
```python
# Bad
result = int(user_input)

# Good
if user_input.isdigit():
    result = int(user_input)
else:
    raise ValueError(f"Invalid input: {user_input}")
```

### TypeError: can only concatenate str (not "int") to str
**Cause**: Mixing string and integer types in concatenation
**Solution**: Convert types explicitly
```python
# Bad
message = "Count: " + count

# Good
message = f"Count: {count}"
# or
message = "Count: " + str(count)
```

### KeyError: 'nonExistentKey'
**Cause**: Accessing dictionary key that doesn't exist
**Solution**: Use safe access methods
```python
# Bad
value = data["key"]

# Good
value = data.get("key", default_value)
# or
if "key" in data:
    value = data["key"]
```

## Infrastructure Errors

### Connection Timeout
**Cause**: Network connectivity issues or service unavailability
**Solution**: Implement retry logic with exponential backoff
```python
from retrying import retry

@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000, stop_max_attempt_number=3)
def make_api_call():
    # API call logic
    pass
```

### DynamoDB Throttling
**Cause**: Exceeding provisioned capacity or burst limits
**Solution**: 
- Use exponential backoff retry
- Consider on-demand billing
- Optimize query patterns

### Lambda Timeout
**Cause**: Function execution exceeds configured timeout
**Solution**:
- Increase timeout limit
- Optimize code performance
- Break down large operations

## Authentication Errors

### Invalid Credentials
**Cause**: Expired or incorrect AWS credentials
**Solution**:
- Check IAM role permissions
- Verify credential rotation
- Use AWS Secrets Manager for sensitive credentials

### Access Denied
**Cause**: Insufficient IAM permissions
**Solution**:
- Review IAM policies
- Use principle of least privilege
- Check resource-based policies

## External Service Errors

### HTTP Connection Errors
**Cause**: Network connectivity issues or external service unavailability
**Solution**:
- Implement retry logic with exponential backoff
- Add circuit breaker pattern
- Set appropriate timeouts
- Monitor external service health

### API Rate Limiting
**Cause**: Exceeding external API rate limits
**Solution**:
- Implement request throttling
- Use caching to reduce API calls
- Add exponential backoff on 429 responses
- Consider API quota management

### Third-party Service Unavailable
**Cause**: External service downtime or degradation
**Solution**:
- Implement graceful degradation
- Use caching where appropriate
- Add fallback mechanisms
- Monitor service health endpoints

## Best Practices for Error Prevention

1. **Input Validation**: Always validate inputs before processing
2. **Error Handling**: Use try-catch blocks with specific exception types
3. **Logging**: Include contextual information in error logs
4. **Monitoring**: Set up CloudWatch alarms for error rates
5. **Testing**: Include error scenarios in unit and integration tests
6. **Documentation**: Keep error handling documentation up to date

## Debugging Tips

1. **Check CloudWatch Logs**: Full execution context is available in logs
2. **Review Stack Traces**: Identify exact line and function causing error
3. **Validate Inputs**: Ensure all required parameters are present and valid
4. **Test Locally**: Reproduce errors in development environment
5. **Monitor Dependencies**: Check status of external services and APIs