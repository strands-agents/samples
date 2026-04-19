# Lambda Troubleshooting Guide

## Step-by-Step Debugging Process

### 1. Initial Error Assessment

#### Gather Basic Information
- **Function Name**: Identify the failing Lambda function
- **Request ID**: Locate the specific invocation ID
- **Error Message**: Extract the primary error message
- **Timestamp**: Note when the error occurred
- **Event Source**: Identify what triggered the function

#### Quick Checks
- Is this a new error or recurring issue?
- Are other functions experiencing similar problems?
- Has there been a recent deployment or configuration change?
- Are there any ongoing AWS service issues?
- What is the error frequency and pattern?

### 2. CloudWatch Logs Analysis

#### Log Investigation Steps
1. **Navigate to CloudWatch Logs**
   - Go to AWS Console → CloudWatch → Log Groups
   - Find `/aws/lambda/[function-name]`
   - Locate the log stream for the specific request ID

2. **Analyze Execution Timeline**
   - Look for START, END, and REPORT log entries
   - Check execution duration vs timeout limit
   - Review memory usage vs allocated memory
   - Identify any custom log entries
   - Note initialization time for cold starts

3. **Stack Trace Analysis**
   - Locate the full stack trace
   - Identify the exact line where error occurred
   - Trace the execution path leading to the error
   - Look for nested exceptions or root causes
   - Check for multiple error occurrences

### 3. Source Code Review

#### Code Analysis Checklist
- **Error Location**: Find the exact line causing the failure
- **Input Validation**: Check if input data is properly validated
- **Null Checks**: Verify null/undefined value handling
- **Exception Handling**: Review try-catch blocks and error handling
- **External Dependencies**: Check external service calls and timeouts

#### Common Code Issues
- Missing null checks before object access
- Improper exception handling
- Hardcoded values instead of environment variables
- Synchronous calls to slow external services
- Inefficient loops or recursive functions
- Missing input validation
- Incorrect data type assumptions

### 4. Configuration Verification

#### Lambda Configuration
- **Memory Allocation**: Sufficient for processing requirements
- **Timeout Setting**: Appropriate for function complexity
- **Environment Variables**: Correctly set and accessible
- **VPC Configuration**: Proper subnet and security group settings
- **IAM Role**: Necessary permissions for all required services
- **Runtime Version**: Compatible with code and dependencies

#### External Dependencies
- **API Endpoints**: Correct URLs and availability
- **Database Connections**: Connection strings and credentials
- **AWS Services**: Proper configuration and permissions
- **Third-party Services**: Authentication and rate limits
- **Network Connectivity**: VPC, NAT gateway, security groups

### 5. Performance Analysis

#### Execution Metrics
- **Duration**: Compare against timeout limit
- **Memory Usage**: Check for memory exhaustion
- **Cold Start Impact**: Measure initialization time
- **Concurrent Executions**: Check for throttling
- **Invocation Frequency**: Analyze patterns

#### Optimization Opportunities
- Reduce deployment package size
- Optimize initialization code
- Implement connection pooling
- Use appropriate memory allocation
- Consider asynchronous processing
- Add caching where appropriate

### 6. Error Resolution Strategies

#### Immediate Fixes
1. **Configuration Updates**
   - Increase memory or timeout if needed
   - Fix environment variables
   - Update IAM permissions
   - Adjust VPC settings

2. **Code Fixes**
   - Add null checks and input validation
   - Improve error handling
   - Fix logic errors or typos
   - Update dependencies

3. **Deployment**
   - Test fixes in development environment
   - Deploy using proper CI/CD pipeline
   - Monitor for successful resolution
   - Verify with test invocations

#### Long-term Improvements
1. **Architecture Enhancements**
   - Implement retry logic with exponential backoff
   - Add circuit breaker patterns
   - Use dead letter queues for failed messages
   - Implement proper monitoring and alerting

2. **Code Quality**
   - Add comprehensive unit tests
   - Implement integration tests
   - Use static code analysis tools
   - Follow coding best practices
   - Add code reviews

### 7. Prevention Strategies

#### Development Practices
- **Input Validation**: Always validate input data
- **Error Handling**: Implement comprehensive error handling
- **Testing**: Write unit and integration tests
- **Code Reviews**: Conduct thorough code reviews
- **Documentation**: Maintain clear documentation

#### Monitoring and Alerting
- **CloudWatch Alarms**: Set up alarms for errors and performance
- **Custom Metrics**: Track business-specific metrics
- **Log Analysis**: Implement log aggregation and analysis
- **Health Checks**: Regular health monitoring for dependencies
- **Dashboards**: Create visibility into function health

#### Operational Excellence
- **Deployment Automation**: Use CI/CD pipelines
- **Environment Parity**: Maintain consistent environments
- **Rollback Procedures**: Have quick rollback capabilities
- **Incident Response**: Establish clear incident response procedures
- **Post-mortems**: Learn from failures

## Common Troubleshooting Scenarios

### Scenario 1: Function Times Out
**Symptoms**: Task timed out after X seconds

**Investigation**:
1. Check CloudWatch logs for execution timeline
2. Identify bottlenecks in processing logic
3. Review external service response times
4. Analyze data processing patterns
5. Check for infinite loops or recursion

**Solutions**:
- Increase timeout setting
- Implement batch processing
- Use asynchronous patterns
- Optimize algorithms
- Add progress logging

### Scenario 2: Permission Denied
**Symptoms**: AccessDenied or UnauthorizedOperation

**Investigation**:
1. Review IAM role policies
2. Check resource ARNs in policies
3. Verify cross-account permissions
4. Test permissions with AWS CLI
5. Check resource-based policies

**Solutions**:
- Add missing IAM permissions
- Fix resource ARN patterns
- Update trust relationships
- Configure VPC endpoints
- Review condition statements

### Scenario 3: External Service Failure
**Symptoms**: Connection errors or HTTP error codes

**Investigation**:
1. Test external service availability
2. Check authentication credentials
3. Review rate limiting and quotas
4. Analyze network connectivity
5. Check service health status

**Solutions**:
- Implement retry logic
- Add circuit breaker pattern
- Update authentication tokens
- Configure proper timeouts
- Add fallback mechanisms

### Scenario 4: Memory Issues
**Symptoms**: Runtime killed or out of memory

**Investigation**:
1. Review memory usage metrics
2. Analyze data processing patterns
3. Check for memory leaks
4. Profile memory allocation
5. Review object lifecycle

**Solutions**:
- Increase memory allocation
- Implement streaming processing
- Optimize data structures
- Add memory monitoring
- Clear large objects

### Scenario 5: Cold Start Latency
**Symptoms**: First invocation much slower

**Investigation**:
1. Measure cold vs warm start times
2. Analyze initialization code
3. Check deployment package size
4. Review dependency imports
5. Profile startup sequence

**Solutions**:
- Minimize package size
- Use Lambda layers
- Optimize initialization
- Consider provisioned concurrency
- Lazy load dependencies

### Scenario 6: Intermittent Failures
**Symptoms**: Random failures, hard to reproduce

**Investigation**:
1. Analyze failure patterns and frequency
2. Check for race conditions
3. Review concurrent execution behavior
4. Test with various input data
5. Monitor external dependencies

**Solutions**:
- Add comprehensive logging
- Implement idempotency
- Handle race conditions
- Add retry logic
- Use correlation IDs

## Debugging Tools and Techniques

### CloudWatch Insights Queries
```
# Find all errors in last hour
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100

# Analyze execution duration
fields @duration
| stats avg(@duration), max(@duration), min(@duration)

# Find timeout errors
fields @timestamp, @message
| filter @message like /Task timed out/
| sort @timestamp desc
```

### X-Ray Tracing
- Enable X-Ray for distributed tracing
- Analyze service maps
- Identify bottlenecks
- Track external service calls
- Measure subsegment performance

### Local Testing
```python
# Test Lambda locally with sample events
import json

def test_lambda_locally():
    with open('test_event.json') as f:
        event = json.load(f)
    
    # Mock context
    class Context:
        aws_request_id = 'test-request-id'
        function_name = 'test-function'
        
    result = lambda_handler(event, Context())
    print(json.dumps(result, indent=2))
```

### Performance Profiling
```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Your function code
    result = process_data()
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
```

## Best Practices for Troubleshooting

1. **Start with logs** - CloudWatch logs contain most information needed
2. **Use correlation IDs** - Track requests across services
3. **Add structured logging** - Makes log analysis easier
4. **Test locally first** - Reproduce issues in development
5. **Monitor metrics** - Set up proactive monitoring
6. **Document solutions** - Build knowledge base of fixes
7. **Use version control** - Track changes and rollback easily
8. **Implement gradual rollouts** - Catch issues early
9. **Have rollback plans** - Quick recovery from bad deploys
10. **Learn from failures** - Conduct post-mortems
