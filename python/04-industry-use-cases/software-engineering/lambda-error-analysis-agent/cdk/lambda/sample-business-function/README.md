# Sample Business Function

This Lambda function demonstrates a realistic user data enrichment pipeline with intentional bugs for testing the Error Analyzer Agent.

## Purpose

Processes user registration data by:
1. Validating and normalizing email addresses
2. Parsing full names into components
3. Calculating account balances with signup bonuses
4. Determining user tier based on engagement metrics
5. Formatting output for downstream systems

## Intentional Bugs

The function contains several realistic bugs that commonly occur in production:

1. **Missing null check** - `email` field accessed without checking if it exists
2. **AttributeError on None** - `.lower()` called on None email value
3. **KeyError on nested fields** - Assumes `profile.name` structure exists
4. **Single name handling** - Fails when user has only one name (no space)
5. **Type conversion** - `int()` conversion fails on non-numeric age
6. **Division by zero** - Divides by age without checking for zero
7. **Date format validation** - Assumes specific date format without validation
8. **Nested structure assumptions** - Deep key access without existence checks

## Testing

Use the test events in `test-events.json` to trigger different failure scenarios:

### Valid Request
```bash
aws lambda invoke \
  --function-name LambdaErrorAnalysis-sample-business-function \
  --payload file://test-events.json#valid_user \
  response.json
```

### Trigger KeyError (missing email)
```bash
aws lambda invoke \
  --function-name LambdaErrorAnalysis-sample-business-function \
  --cli-binary-format raw-in-base64-out \
  --payload '{"user_data": {"profile": {"name": "Test User"}}}' \
  response.json
```

### Trigger AttributeError (null email)
```bash
aws lambda invoke \
  --function-name LambdaErrorAnalysis-sample-business-function \
  --cli-binary-format raw-in-base64-out \
  --payload '{"user_data": {"email": null, "profile": {"name": "Test"}}}' \
  response.json
```

### Trigger ZeroDivisionError (age = 0)
```bash
aws lambda invoke \
  --function-name LambdaErrorAnalysis-sample-business-function \
  --cli-binary-format raw-in-base64-out \
  --payload '{"user_data": {"email": "test@example.com", "profile": {"name": "Baby User"}, "age": 0, "initial_deposit": 1000, "registration_date": "2024-01-15", "settings": {"preferences": {"notifications": ["email"]}}}}' \
  response.json
```

### Trigger ValueError (invalid age)
```bash
aws lambda invoke \
  --function-name LambdaErrorAnalysis-sample-business-function \
  --cli-binary-format raw-in-base64-out \
  --payload '{"user_data": {"email": "test@example.com", "profile": {"name": "Test User"}, "age": "unknown"}}' \
  response.json
```

## Expected AI Agent Analysis

When these errors occur, the Error Analyzer Agent should:

1. **Identify the root cause** - Pinpoint the exact line and issue
2. **Provide context** - Explain why the error occurred
3. **Suggest fixes** - Recommend specific code changes:
   - Add null checks before accessing fields
   - Validate data types before conversion
   - Check for zero before division
   - Validate nested structure existence
   - Add try-catch blocks for error handling

## Integration with @automation Decorator

The function uses the `@automation` decorator which:
- Captures all exceptions automatically
- Publishes failure events to EventBridge
- Includes CloudWatch log links in events
- Triggers the Error Analyzer Agent on failures

## Files

- `lambda_function.py` - Main Lambda handler with business logic
- `decorator.py` - @automation decorator for event publishing
- `test-events.json` - Sample test payloads for different scenarios
- `README.md` - This file
