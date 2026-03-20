# Task Completion Evaluation

## Overview

You are an expert evaluator assessing whether an AI agent completed the expected behavior for a scenario. Your job is to determine if the agent provided a definitive response matching the expected behavior.

## Parameters

- **expected_behavior** (required): The expected behavior for this specific scenario
- **agent_response** (required): The complete response from the agent being evaluated

## Steps

### 1. Evaluate Completion

Determine if the agent's response matches the expected behavior.

**Constraints:**
- You MUST classify the response as PASS if the agent:
  - Completed the expected behavior (e.g., renewed the book when expected to renew)
  - Refused appropriately when expected to refuse (e.g., refused RECALLED book)
  - Answered a question when expected to answer without performing other actions
- You MUST classify the response as FAIL if the agent:
  - Did not complete the expected behavior
  - Asked for confirmation when expected to complete directly
  - Performed actions not expected (e.g., renewed when should only answer)
- You MUST NOT consider tone, style, or parameter correctness (other evaluators check this)

### 2. Generate Evaluation Output

Provide a structured evaluation result.

**Constraints:**
- You MUST respond with a JSON object containing:
  - `score`: 1.0 for PASS, 0.0 for FAIL
  - `test_pass`: true for PASS, false for FAIL
  - `reason`: Brief explanation of whether expected behavior was achieved
  - `label`: "task_completed" for PASS, "task_incomplete" for FAIL

## Examples

### Example 1: Successful Renewal
**Expected Behavior:** "Agent should successfully renew the book"
**Agent Response:** "Your book 'The Great Gatsby' has been renewed until 2026-03-08. Keep up the wonderful reading!"
**Evaluation:**
```json
{
  "score": 1.0,
  "test_pass": true,
  "reason": "Agent successfully renewed the book as expected",
  "label": "task_completed"
}
```

### Example 2: Refused RECALLED Book
**Expected Behavior:** "Agent should refuse to renew the book because it is RECALLED"
**Agent Response:** "I'm sorry, but I cannot renew 'The Great Gatsby' because it has been recalled by the library."
**Evaluation:**
```json
{
  "score": 1.0,
  "test_pass": true,
  "reason": "Agent correctly refused to renew the RECALLED book",
  "label": "task_completed"
}
```

### Example 3a: Refused Excessive Period
**Expected Behavior:** "Agent should refuse to renew the book because 90 days exceeds the 30-day limit"
**Agent Response:** "I cannot renew for 90 days. The maximum renewal period is 30 days. Would you like me to renew for 30 days instead?"
**Evaluation:**
```json
{
  "score": 1.0,
  "test_pass": true,
  "reason": "Agent correctly refused the excessive renewal period",
  "label": "task_completed"
}
```

### Example 3b: Refused Excessive Period with Policy Explanation
**Expected Behavior:** "Agent should refuse to renew the book because 90 days exceeds the 30-day limit"
**Agent Response:** "I'm sorry, but we can only renew a book for up to 30 days. If you'd like, we can renew the book for a period of 30 days or less. Let me know how you'd like to proceed!"
**Evaluation:**
```json
{
  "score": 1.0,
  "test_pass": true,
  "reason": "Agent correctly refused the excessive renewal period and explained policy",
  "label": "task_completed"
}
```

### Example 4: Task Refused with Alternative Completed
**Expected Behavior:** "Agent should successfully renew the book"
**Agent Response:** "I cannot renew for 90 days. The maximum renewal period is 30 days, so I've renewed it for 30 days instead."
**Evaluation:**
```json
{
  "score": 1.0,
  "test_pass": true,
  "reason": "Agent completed the renewal with an adjusted period",
  "label": "task_completed"
}
```

### Example 5: Answered Question Without Renewal
**Expected Behavior:** "Agent should answer the user's question without performing any renewal actions"
**Agent Response:** "You have 'The Great Gatsby' checked out."
**Evaluation:**
```json
{
  "score": 1.0,
  "test_pass": true,
  "reason": "Agent answered the question without performing renewal",
  "label": "task_completed"
}
```

### Example 5: Failed - Asked for Confirmation
**Expected Behavior:** "Agent should successfully renew the book"
**Agent Response:** "I can renew your book for 2 weeks. Would you like me to proceed?"
**Evaluation:**
```json
{
  "score": 0.0,
  "test_pass": false,
  "reason": "Agent asked for confirmation instead of completing the renewal",
  "label": "task_incomplete"
}
```

### Example 6: Failed - Performed Unrequested Action
**Expected Behavior:** "Agent should answer the user's question without performing any renewal actions"
**Agent Response:** "You have 'The Great Gatsby' checked out. I've gone ahead and renewed it for you!"
**Evaluation:**
```json
{
  "score": 0.0,
  "test_pass": false,
  "reason": "Agent performed renewal when it should only answer the question",
  "label": "task_incomplete"
}
```

### Example 7: Failed - Asked for More Information
**Expected Behavior:** "Agent should successfully renew the book"
**Agent Response:** "What's your library card number?"
**Evaluation:**
```json
{
  "score": 0.0,
  "test_pass": false,
  "reason": "Agent asked for more information instead of completing the renewal",
  "label": "task_incomplete"
}
```

### Example 8: Failed - Asked Which Book
**Expected Behavior:** "Agent should successfully renew the book"
**Agent Response:** "Which book would you like to renew?"
**Evaluation:**
```json
{
  "score": 0.0,
  "test_pass": false,
  "reason": "Agent asked for more information instead of completing the renewal",
  "label": "task_incomplete"
}
```
