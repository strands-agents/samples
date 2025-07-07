# Bedrock Knowledge Base with DynamoDB Integration

Build an intelligent agent that combines Amazon Bedrock Knowledge Base for retrieval-augmented generation (RAG) with DynamoDB for persistent data operations, creating a comprehensive information and transaction system.

Learn more about this pattern at Serverless Land Patterns: [Link will be generated]

**Important:** this application uses various AWS services and there are costs associated with these services after the Free Tier usage - please see the [AWS Pricing page](https://aws.amazon.com/pricing/) for details. You are responsible for any AWS costs incurred. No warranty is implied in this example.

## Requirements

* [AWS CLI](https://aws.amazon.com/cli/) installed and configured
* Python 3.10 or later
* Strands Agents SDK
* AWS IAM permissions for:
  * Amazon Bedrock Knowledge Base
  * Amazon DynamoDB
  * Amazon S3
  * AWS Systems Manager Parameter Store

## Deployment Instructions

1. Create a new directory and install dependencies
    ```bash
    mkdir bedrock-kb-dynamodb && cd bedrock-kb-dynamodb
    pip install strands-agents strands-agents-tools boto3 pandas
    ```

2. Deploy AWS infrastructure (Knowledge Base and DynamoDB)
    ```bash
    # Copy the prereqs directory from this pattern
    cd prereqs
    chmod +x deploy_prereqs.sh
    ./deploy_prereqs.sh
    ```

3. Copy the source code files from this pattern

4. Run the agent:
    ```bash
    python src/agent.py
    ```

## How it works

This pattern demonstrates a sophisticated agent architecture that combines:

### Core Components

1. **Amazon Bedrock Knowledge Base**: Provides RAG capabilities for retrieving information from uploaded documents
2. **Amazon DynamoDB**: Handles persistent data operations (CRUD operations)
3. **Custom Tools**: Bridge between the agent and AWS services
4. **Built-in Tools**: Time awareness and knowledge retrieval

### Architecture Flow

```
User Query → Strands Agent → [Knowledge Base OR DynamoDB Tools] → AWS Services → Response
```

### Tool Integration Approaches

The pattern demonstrates two approaches for creating custom tools:

#### 1. Decorator Approach (Simple)
```python
@tool
def get_item_details(item_id: str) -> dict:
    """Get item details from DynamoDB"""
    # Implementation
```

#### 2. Tool Specification Approach (Advanced)
```python
TOOL_SPEC = {
    "name": "create_item",
    "description": "Create a new item",
    "inputSchema": {
        # Detailed schema definition
    }
}
```

### Key Features

- **Knowledge Retrieval**: Uses Bedrock Knowledge Base for document-based Q&A
- **Data Persistence**: DynamoDB operations for creating, reading, updating, deleting records
- **Intelligent Routing**: Agent automatically chooses between knowledge retrieval and data operations
- **Error Handling**: Robust error handling for AWS service interactions
- **Conversation Context**: Maintains conversation flow across multiple interactions

## Architecture Components

1. **Strands Agent**: Orchestrates the entire workflow with intelligent decision-making
2. **Amazon Bedrock**: Provides the foundation model for natural language understanding
3. **Knowledge Base**: Stores and retrieves relevant information from documents
4. **DynamoDB Table**: Handles structured data persistence
5. **Systems Manager**: Stores configuration parameters securely

## Testing

1. Deploy the infrastructure:
    ```bash
    cd prereqs && ./deploy_prereqs.sh
    ```

2. Run the agent:
    ```bash
    python src/agent.py
    ```

3. Try these example interactions:
    - **Knowledge Base Query**: "What information do you have about [your document topic]?"
    - **Create Record**: "Create a new booking for tonight at 8pm"
    - **Retrieve Record**: "Get details for booking ID [booking-id]"
    - **Delete Record**: "Cancel booking [booking-id]"
    - **Mixed Query**: "Tell me about the menu and make a reservation"

## Customization

### Adding Your Own Documents

1. Upload documents to the S3 bucket created by the infrastructure
2. Sync the Knowledge Base to index new documents
3. Update the agent's system prompt if needed

### Modifying DynamoDB Schema

1. Update the table schema in `prereqs/dynamodb.py`
2. Modify the custom tools to match your schema
3. Update the agent's system prompt with new field descriptions

## Cleanup

When done testing, clean up the AWS resources:

```bash
cd prereqs
chmod +x cleanup.sh
./cleanup.sh
```

## Next Steps

Consider these enhancements:
- Add multiple Knowledge Bases for different domains
- Implement conversation memory for better context
- Add authentication and authorization
- Deploy as a serverless application using Lambda
- Add monitoring and logging with CloudWatch
- Implement data validation and sanitization
- Add support for file uploads and processing

## Documentation
- [Strands Agents Documentation](https://strandsagents.com/)
- [Amazon Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [Amazon DynamoDB](https://docs.aws.amazon.com/dynamodb/)
- [Custom Tools Guide](https://strandsagents.com/latest/user-guide/concepts/tools/custom-tools/)

## License

This project is licensed under the MIT-0 License. See the LICENSE file. 