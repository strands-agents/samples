# Guardrails AI Integration
Example for integrating Strands Agent with [Guardrails AI](https://www.guardrailsai.com/) for cloud-based content moderation and safety guardrails.

Guardrails AI provides a comprehensive platform for implementing various safety checks including toxic language detection, bias detection, and content filtering.

## Prerequisites

1. Sign up for [Guardrails AI](https://www.guardrailsai.com/)
2. Create an API key in your Guardrails AI dashboard
3. Python 3.8+ installed

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Add Guardrails API key
```
guardrails configure
```

Enable remote inferencing and add your API key.

3. Install the toxic language guardrail:
```bash
guardrails hub install hub://guardrails/toxic_language
```

## Usage

Run the example:
```bash
python main.py
```

The agent will use Guardrails AI to check for toxic language and other harmful content.
```
✓ User message passed all guardrail checks
Hello! I'm doing well, thank you for asking. How can I assist you today?Processing message: {'role': 'assistant', 'content': [{'text': "Hello! I'm doing well, thank you for asking. How can I assist you today?"}]}
✓ Assistant response processed normally
Hello! I'm doing well, thank you for asking. How can I assist you today?

🚫 BLOCKING MESSAGE: Validation failed for field with errors: The following sentences in your response were found to be toxic:

- Actually I dont care, f**k you

🚫 REQUEST BLOCKED
==================================================
Your message was blocked due to policy violations.
Reason: The content contains inappropriate or harmful language.
Please rephrase your request using respectful language.
```

## Files

- `main.py` - Strands Agent with Guardrails AI hook integration
- `guardrail.py` - Guardrails AI implementation and validation logic
- `requirements.txt` - Python dependencies including guardrails-ai

## How It Works

The example uses Strands Agent hooks to intercept messages and validate them against Guardrails AI's toxic language detection model. Content that violates the guardrails is blocked or modified before processing.

## Available Guardrails
You can install additional guardrails from the Guardrails AI hub:
- `hub://guardrails/toxic_language` - Detects toxic and harmful language
- `hub://guardrails/sensitive_topics` - Filters sensitive topic discussions  
- `hub://guardrails/bias_check` - Identifies potential bias in content

See the [Guardrails AI Hub](https://hub.guardrailsai.com/) for more options.


