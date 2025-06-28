# Strands HR Assistant

A virtual HR assistant built with the Strands SDK that helps employees manage their time off requests.

## Features

- Check time off balance
- Submit time off requests
- Natural language interaction

## Prerequisites

- Python 3.10 or higher
- AWS account with access to Amazon Bedrock
- AWS CLI configured with appropriate credentials

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/strands-agents/samples.git
   cd strands-samples/01-tutorials/01-fundamentals/09-human-in-the-loop
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Configure AWS credentials:
   - Make sure you have the AWS CLI installed and configured with your credentials
   - Update the `aws_config.py` file with your AWS region and profile name

## Configuration

The HR assistant is configured using the `BedrockAgentStack/config.json` file. You can modify the following settings:

- `agentName`: The name of the HR assistant
- `agentDescription`: A description of the HR assistant
- `agentInstruction`: Instructions for the HR assistant
- Function names and descriptions

## Usage

1. Run the HR assistant:
   ```
   python hr_assistant.py
   ```

2. Interact with the assistant using natural language:
   - "What is my time off balance?"
   - "I want to request time off from 2025-07-01 for 5 days"
   - "Show me my pending time off requests"

3. Type 'exit' to quit the assistant.

## How It Works

The HR assistant uses the Strands SDK to create an agent with two main functions:

1. `get_time_off()`: Retrieves the employee's time off balance
2. `request_time_off(start_date, number_of_days)`: Submits a time off request

The agent uses Amazon Bedrock's Claude model to understand natural language requests and determine when to call these functions.

## Customization

You can extend the HR assistant by adding more functions to handle additional HR-related tasks, such as:

- Checking pay information
- Updating personal details
- Submitting expense reports
- Accessing company policies

To add a new function, define it using the `@tool` decorator and add it to the agent's tools list in the `create_hr_assistant()` function.

## Troubleshooting

- **AWS Credentials Error**: Make sure your AWS credentials are properly configured and you have access to Amazon Bedrock.
- **Model Not Found**: Verify that the model ID in the code matches an available model in your AWS region.
- **Function Not Called**: Ensure that your natural language request clearly indicates which function should be called.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
