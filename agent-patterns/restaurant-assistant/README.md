# Restaurant Assistant with Bedrock Knowledge Base

A restaurant assistant agent that helps customers make reservations and query restaurant information using Amazon Bedrock Knowledge Base and DynamoDB. This pattern demonstrates how to create a conversational agent that can handle restaurant bookings, menu queries, and reservation management.

Learn more about this pattern at Strands Agents Patterns: [Link will be generated]

**Important:** this application uses various AWS services and there are costs associated with these services after the Free Tier usage - please see the [AWS Pricing page](https://aws.amazon.com/pricing/) for details. You are responsible for any AWS costs incurred. No warranty is implied in this example.

## Requirements

* [AWS CLI](https://aws.amazon.com/cli/) installed and configured
* Python 3.10 or later
* Strands Agents SDK
* AWS Account with access to:
  * Amazon Bedrock (Claude 3.7 Sonnet model)
  * Amazon DynamoDB
  * Amazon Bedrock Knowledge Base
  * AWS Systems Manager Parameter Store

## Deployment Instructions

1. Create a new directory, navigate to it and install dependencies
    ```
    mkdir restaurant-assistant && cd restaurant-assistant
    pip install -r requirements.txt
    ```

2. Deploy the prerequisite AWS infrastructure
    ```
    sh deploy_prereqs.sh
    ```
    This will create:
    - Amazon Bedrock Knowledge Base for restaurant information
    - DynamoDB table for reservations
    - SSM parameters for configuration

3. Configure your environment
    ```python
    import os
    import boto3

    # Set up AWS resources
    kb_name = "restaurant-assistant"
    dynamodb = boto3.resource("dynamodb")
    smm_client = boto3.client("ssm")
    
    # Get configuration from SSM
    table_name = smm_client.get_parameter(Name=f"{kb_name}-table-name")
    kb_id = smm_client.get_parameter(Name=f"{kb_name}-kb-id")
    ```

## How it works

The Restaurant Assistant pattern demonstrates:

1. **Single agent architecture** with multiple tool integrations
2. **AWS Service Integration**
   - Amazon Bedrock Knowledge Base for restaurant/menu information
   - DynamoDB for reservation management
   - Bedrock Claude 3.7 as the underlying LLM

3. **Tool Implementation Approaches**
   - Decorator-based tools (`get_booking_details`)
   - TOOL_SPEC approach (`create_booking`)
   - Module-based tools (`delete_booking`)

4. **Conversational Flow**
   - Natural language understanding
   - Follow-up questions for missing information
   - Contextual responses

![Architecture](images/architecture.png)

## Testing

1. Start with a basic query about restaurants:
    ```python
    results = agent("Hi, where can I eat in San Francisco?")
    ```

2. Make a reservation:
    ```python
    results = agent("Make a reservation for tonight at Rice & Spice")
    # Agent will ask follow-up questions for missing details
    results = agent("At 8pm, for 4 people in the name of Anna")
    ```

3. Check or cancel reservations:
    ```python
    results = agent("What are the details for my booking?")
    results = agent("Cancel my reservation")
    ```

## Cleanup

1. Run the cleanup script to remove AWS resources:
    ```
    sh cleanup.sh
    ```

2. This will delete:
   - Knowledge Base
   - DynamoDB table
   - SSM parameters

## Next Steps

1. Extend the pattern:
   - Add payment processing
   - Implement table availability checking
   - Add multi-restaurant support
   - Integrate with real restaurant APIs

2. Enhance the agent:
   - Add memory for user preferences
   - Implement authentication
   - Add more sophisticated conversation handling

## Documentation
- [Strands Agents Documentation](https://strandsagents.com/)
- [Amazon Bedrock Knowledge Base](https://aws.amazon.com/bedrock/knowledge-bases/)
- [Amazon DynamoDB](https://aws.amazon.com/dynamodb/)
- [AWS Systems Manager Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)

## License

This project is licensed under the MIT-0 License. See the LICENSE file. 