# User Data Validation Error Patterns

## Overview
This document covers common validation errors in user data processing Lambda functions, specifically for user registration and profile enrichment workflows.

## Common User Data Validation Errors

### 1. Missing Required Email Field
**Error Pattern**: `KeyError: 'email'`

**Test Case**: `missing_email`
```json
{
  "user_data": {
    "profile": {"name": "Jane Smith"},
    "age": 25
  }
}
```

**Root Cause**: 
- Function attempts to access `user_data['email']` without checking if the key exists
- Common in user registration flows where email is expected but not validated upfront

**Stack Trace Pattern**:
```python
email = user_data['email'].lower().strip()
           ~~~~~~~~~^^^^^^^^
KeyError: 'email'
```

**Recommended Fix**:
```python
# Option 1: Validate required fields upfront
def validate_required_fields(user_data):
    required_fields = ['email', 'profile', 'age']
    missing = [field for field in required_fields if field not in user_data]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

# Option 2: Use .get() with validation
email = user_data.get('email')
if not email:
    raise ValueError("Email is required for user registration")
email = email.lower().strip()

# Option 3: Use .get() with default
email = user_data.get('email', '').lower().strip()
if not email:
    logger.warning("No email provided, using placeholder")
    email = f"unknown_{int(time.time())}@example.com"
```

**Prevention**:
- Add schema validation at function entry point
- Use Pydantic models for type checking
- Implement API Gateway request validation
- Add unit tests for missing field scenarios

---

### 2. Null Email Value
**Error Pattern**: `AttributeError: 'NoneType' object has no attribute 'lower'`

**Test Case**: `null_email`
```json
{
  "user_data": {
    "email": null,
    "profile": {"name": "Bob Johnson"}
  }
}
```

**Root Cause**:
- Email field exists but contains `null` value
- Code attempts to call `.lower()` on None type
- Different from missing key - the key exists but value is None

**Stack Trace Pattern**:
```python
email = user_data['email'].lower().strip()
        ~~~~~~~~~~~~~~~~~~^^^^^^^
AttributeError: 'NoneType' object has no attribute 'lower'
```

**Recommended Fix**:
```python
# Check for None explicitly
email = user_data.get('email')
if email is None or not email:
    raise ValueError("Email cannot be null or empty")
email = email.lower().strip()

# Or use defensive programming
email = user_data.get('email') or ''
if not email:
    raise ValueError("Valid email is required")
email = email.lower().strip()
```

**Prevention**:
- Validate not just presence but also non-null values
- Use type hints and runtime validation
- Add null checks before string operations

---

### 3. Missing Nested Profile Data
**Error Pattern**: `KeyError: 'profile'` or `KeyError: 'name'`

**Test Case**: `missing_profile`
```json
{
  "user_data": {
    "email": "alice@example.com",
    "age": 28
  }
}
```

**Root Cause**:
- Nested dictionary access without validation
- Code assumes profile structure exists
- Common when processing optional nested data

**Stack Trace Pattern**:
```python
full_name = user_data['profile']['name']
            ~~~~~~~~~^^^^^^^^^^^
KeyError: 'profile'
```

**Recommended Fix**:
```python
# Safe nested access
profile = user_data.get('profile', {})
name = profile.get('name', 'Unknown')

# Or validate structure
if 'profile' not in user_data or 'name' not in user_data['profile']:
    raise ValueError("User profile with name is required")
full_name = user_data['profile']['name']

# Using helper function
def safe_get_nested(data, *keys, default=None):
    """Safely get nested dictionary values"""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data

name = safe_get_nested(user_data, 'profile', 'name', default='Unknown')
```

**Prevention**:
- Use safe nested access patterns
- Validate nested structure upfront
- Consider flattening data structures
- Use libraries like `glom` for complex nested access

---

### 4. Single Name Handling
**Error Pattern**: `IndexError: list index out of range`

**Test Case**: `single_name`
```json
{
  "user_data": {
    "email": "madonna@example.com",
    "profile": {"name": "Madonna"},
    "age": 35
  }
}
```

**Root Cause**:
- Code assumes name can be split into first/last
- Single names (Madonna, Cher, etc.) cause split to return single element
- Accessing `name_parts[1]` fails

**Stack Trace Pattern**:
```python
name_parts = full_name.split()
first_name = name_parts[0]
last_name = name_parts[1]  # IndexError if only one name
          ~~~~~~~~~~^^^
IndexError: list index out of range
```

**Recommended Fix**:
```python
# Handle single names gracefully
name_parts = full_name.split()
first_name = name_parts[0] if name_parts else ''
last_name = name_parts[1] if len(name_parts) > 1 else ''

# Or use maxsplit
name_parts = full_name.split(maxsplit=1)
first_name = name_parts[0] if name_parts else ''
last_name = name_parts[1] if len(name_parts) > 1 else ''

# Or handle explicitly
if len(name_parts) == 1:
    first_name = name_parts[0]
    last_name = ''
elif len(name_parts) >= 2:
    first_name = name_parts[0]
    last_name = ' '.join(name_parts[1:])  # Handle multiple last names
```

**Prevention**:
- Never assume array/list length
- Always check bounds before accessing indices
- Consider cultural naming conventions
- Add test cases for edge cases

---

### 5. Invalid Age Type
**Error Pattern**: `TypeError: '>' not supported between instances of 'str' and 'int'`

**Test Case**: `invalid_age`
```json
{
  "user_data": {
    "email": "test@example.com",
    "profile": {"name": "Test User"},
    "age": "unknown"
  }
}
```

**Root Cause**:
- Age field contains string instead of integer
- Type coercion not performed before comparison
- JSON parsing may preserve string types

**Stack Trace Pattern**:
```python
if user_data['age'] > 18:
   ~~~~~~~~~~~~~~~~^^^
TypeError: '>' not supported between instances of 'str' and 'int'
```

**Recommended Fix**:
```python
# Validate and convert type
try:
    age = int(user_data.get('age', 0))
except (ValueError, TypeError):
    raise ValueError(f"Invalid age value: {user_data.get('age')}")

if age < 0 or age > 150:
    raise ValueError(f"Age must be between 0 and 150, got: {age}")

# Or use type checking
age = user_data.get('age')
if not isinstance(age, int):
    try:
        age = int(age)
    except (ValueError, TypeError):
        raise ValueError(f"Age must be a number, got: {type(age).__name__}")
```

**Prevention**:
- Use Pydantic for automatic type validation
- Add explicit type conversion
- Validate data types at entry point
- Use type hints with runtime validation

---

### 6. Zero or Negative Age
**Error Pattern**: `ValueError: Age must be positive`

**Test Case**: `zero_age`
```json
{
  "user_data": {
    "email": "baby@example.com",
    "profile": {"name": "Baby User"},
    "age": 0
  }
}
```

**Root Cause**:
- Business logic requires positive age
- Zero is technically valid but not for business rules
- Need to distinguish between missing and invalid values

**Recommended Fix**:
```python
# Validate business rules
age = user_data.get('age')
if age is None:
    raise ValueError("Age is required")
if not isinstance(age, int) or age <= 0:
    raise ValueError(f"Age must be a positive integer, got: {age}")
if age > 150:
    raise ValueError(f"Age seems unrealistic: {age}")

# Or with more context
def validate_age(age):
    """Validate age meets business requirements"""
    if age is None:
        raise ValueError("Age is required for registration")
    if not isinstance(age, (int, float)):
        raise TypeError(f"Age must be numeric, got {type(age).__name__}")
    if age < 1:
        raise ValueError("Age must be at least 1 year")
    if age > 120:
        raise ValueError(f"Age {age} exceeds maximum allowed (120)")
    return int(age)
```

**Prevention**:
- Define clear business rules for validation
- Separate technical validation from business validation
- Document acceptable ranges
- Add boundary value tests

---

### 7. Invalid Date Format
**Error Pattern**: `ValueError: time data '01/15/2024' does not match format '%Y-%m-%d'`

**Test Case**: `invalid_date_format`
```json
{
  "user_data": {
    "email": "user@example.com",
    "profile": {"name": "Date User"},
    "age": 25,
    "registration_date": "01/15/2024"
  }
}
```

**Root Cause**:
- Date format doesn't match expected format
- Multiple date formats in use (MM/DD/YYYY vs YYYY-MM-DD)
- No format validation before parsing

**Stack Trace Pattern**:
```python
date_obj = datetime.strptime(user_data['registration_date'], '%Y-%m-%d')
ValueError: time data '01/15/2024' does not match format '%Y-%m-%d'
```

**Recommended Fix**:
```python
# Try multiple formats
def parse_date_flexible(date_str):
    """Parse date with multiple format support"""
    formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date: {date_str}. Expected formats: YYYY-MM-DD or MM/DD/YYYY")

# Or use dateutil
from dateutil import parser
try:
    date_obj = parser.parse(user_data['registration_date'])
except (ValueError, TypeError) as e:
    raise ValueError(f"Invalid date format: {user_data['registration_date']}")

# Or enforce single format
try:
    date_obj = datetime.strptime(user_data['registration_date'], '%Y-%m-%d')
except ValueError:
    raise ValueError(f"Date must be in YYYY-MM-DD format, got: {user_data['registration_date']}")
```

**Prevention**:
- Standardize on ISO 8601 format (YYYY-MM-DD)
- Use flexible parsing libraries
- Document expected formats clearly
- Validate at API Gateway level

---

### 8. Missing Nested Settings
**Error Pattern**: `KeyError: 'preferences'` or `TypeError: 'NoneType' object is not subscriptable`

**Test Case**: `missing_nested_settings`
```json
{
  "user_data": {
    "email": "user@example.com",
    "profile": {"name": "Settings User"},
    "age": 30,
    "registration_date": "2024-01-15",
    "settings": {}
  }
}
```

**Root Cause**:
- Deep nested access without validation
- Empty objects vs missing keys
- Assumptions about data structure

**Stack Trace Pattern**:
```python
notifications = user_data['settings']['preferences']['notifications']
                ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
KeyError: 'preferences'
```

**Recommended Fix**:
```python
# Safe nested access with defaults
settings = user_data.get('settings', {})
preferences = settings.get('preferences', {})
notifications = preferences.get('notifications', ['email'])  # default

# Or use helper
def get_nested(data, *keys, default=None):
    """Safely navigate nested dictionaries"""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
            if data is None:
                return default
        else:
            return default
    return data if data is not None else default

notifications = get_nested(
    user_data, 
    'settings', 'preferences', 'notifications',
    default=['email']
)

# Or validate structure
required_structure = {
    'settings': {
        'preferences': {
            'notifications': list
        }
    }
}
# Use schema validation library
```

**Prevention**:
- Use schema validation (Pydantic, JSON Schema)
- Provide sensible defaults for optional nested data
- Document data structure requirements
- Use helper functions for nested access

---

## General Best Practices for User Data Validation

### 1. Validate Early
```python
def lambda_handler(event, context):
    # Validate immediately
    user_data = event.get('user_data', {})
    validate_user_data(user_data)
    
    # Then process
    return process_user(user_data)
```

### 2. Use Schema Validation
```python
from pydantic import BaseModel, EmailStr, Field

class UserProfile(BaseModel):
    name: str = Field(min_length=1)

class UserData(BaseModel):
    email: EmailStr
    profile: UserProfile
    age: int = Field(gt=0, le=150)
    registration_date: str = Field(regex=r'^\d{4}-\d{2}-\d{2}$')
    
def lambda_handler(event, context):
    try:
        user = UserData(**event['user_data'])
    except ValidationError as e:
        return {'error': str(e)}
```

### 3. Provide Clear Error Messages
```python
# Bad
raise ValueError("Invalid data")

# Good
raise ValueError(
    f"Invalid email format: '{email}'. "
    f"Expected format: user@domain.com"
)
```

### 4. Log Validation Failures
```python
logger.info(f"Validating user data for: {user_data.get('email', 'unknown')}")
try:
    validate_user_data(user_data)
except ValueError as e:
    logger.error(f"Validation failed: {e}", extra={'user_data': user_data})
    raise
```

### 5. Test All Edge Cases
```python
# Test cases should cover:
# - Missing required fields
# - Null values
# - Wrong types
# - Empty strings
# - Boundary values
# - Invalid formats
# - Nested structure issues
```

## Error Recovery Strategies

### Graceful Degradation
```python
# Use defaults for optional fields
email = user_data.get('email', 'noreply@example.com')
age = user_data.get('age', 0)
```

### Partial Success
```python
# Process what you can, log what you can't
results = {
    'processed': [],
    'failed': []
}
for field in fields:
    try:
        process_field(field)
        results['processed'].append(field)
    except Exception as e:
        results['failed'].append({'field': field, 'error': str(e)})
```

### Retry with Correction
```python
# Attempt to fix common issues
email = user_data.get('email', '').strip().lower()
if not email:
    # Try alternate fields
    email = user_data.get('contact_email') or user_data.get('username')
```

## Monitoring and Alerting

### Key Metrics to Track
- Validation failure rate by field
- Most common missing fields
- Type mismatch frequency
- Invalid format patterns

### CloudWatch Metrics
```python
cloudwatch.put_metric_data(
    Namespace='UserValidation',
    MetricData=[{
        'MetricName': 'ValidationFailures',
        'Value': 1,
        'Unit': 'Count',
        'Dimensions': [
            {'Name': 'FieldName', 'Value': 'email'},
            {'Name': 'ErrorType', 'Value': 'Missing'}
        ]
    }]
)
```
