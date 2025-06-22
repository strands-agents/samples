# Unstructured-Structured RAG Agent

This project demonstrates how to build an intelligent RAG (Retrieval-Augmented Generation) system that can route queries between structured and unstructured knowledge bases using Amazon Bedrock Agents and Strands framework.

## 📋 Overview

The system consists of:
- **Unstructured Knowledge Base**: Handles document-based, narrative, and conceptual queries
- **Structured Knowledge Base**: Manages data analysis, metrics, and quantitative queries using Redshift
- **Intelligent Routing Agent**: Uses Strands framework to automatically route queries to the appropriate knowledge base

## 🏗️ Architecture

```
┌─────────────────┐
│   User Query    │
└─────────┬───────┘
          │
    ┌─────▼─────┐
    │ Strands   │
    │ Router    │
    │ Agent     │
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │ Decision  │
    │ Logic     │
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │  Route    │
    │  Query    │
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │           │
    ▼           ▼
┌─────────┐ ┌──────────┐
│Unstr.   │ │Struct.   │
│KB       │ │KB        │
│(Docs)   │ │(Redshift)│
└─────────┘ └──────────┘
```

## 📁 Project Structure

```
2-unstructure-structured-rag_agent/
├── 0-prerequisites.ipynb           # Setup AWS infrastructure
├── 2-unstructured-structured-rag-agent.ipynb  # Main implementation
├── utils/
│   └── structured_knowledge_base.py  # Utility for Bedrock KB setup
└── sample_data/
    ├── orders.csv                  # Sample e-commerce orders
    ├── order_items.csv             # Sample order items
    ├── payments.csv                # Sample payment records
    └── reviews.csv                 # Sample customer reviews
```

## 🚀 Getting Started

### Prerequisites

- AWS Account with appropriate permissions
- Python 3.8+
- Jupyter Notebook environment
- Strands framework

### Required AWS Services

- Amazon Bedrock (with agent runtime)
- Amazon Redshift Serverless
- Amazon S3
- AWS IAM

### Installation

1. **Install dependencies:**
   ```bash
   pip install boto3 strands
   ```

2. **Configure AWS credentials:**
   ```bash
   aws configure
   ```

3. **Run the prerequisites notebook:**
   - Open `0-prerequisites.ipynb`
   - Execute all cells to set up AWS infrastructure

### Step-by-Step Setup

#### 1. Infrastructure Setup (`0-prerequisites.ipynb`)

This notebook creates:
- **Redshift Serverless**: Namespace and workgroup for structured data
- **S3 Bucket**: For data staging
- **Database Tables**: Orders, order_items, payments, reviews
- **IAM Roles**: For service permissions
- **Bedrock Knowledge Base**: Configured with Redshift as data source

#### 2. Agent Implementation (`2-unstructured-structured-rag-agent.ipynb`)

This notebook demonstrates:
- **Tool Creation**: Separate tools for structured and unstructured queries
- **Agent Configuration**: Using Strands framework for intelligent routing
- **Query Examples**: Business strategy vs. financial data queries

## 🔧 Configuration

### Knowledge Base IDs

Update the knowledge base IDs in the main notebook:

```python
UNSTRUCTURED_KB_ID = "YOUR_UNSTRUCTURED_KB_ID"  # Document-based KB
STRUCTURED_KB_ID = "YOUR_STRUCTURED_KB_ID"      # SQL/Redshift KB
```

### AWS Region

Set your preferred AWS region:

```python
region = boto3.Session().region_name or "us-west-2"
```

## 🛠️ Usage

### Running Queries

The system automatically routes queries based on their content:

**Unstructured Queries** (routed to document KB):
```python
response = orchestrator("What is Octank Financial's business strategy?")
```

**Structured Queries** (routed to Redshift KB):
```python
response = orchestrator("What is the total spending by all customers?")
```

### Query Types

| Query Type | Knowledge Base | Examples |
|------------|----------------|----------|
| **Unstructured** | Document-based | Business strategies, policies, company culture |
| **Structured** | Redshift/SQL | Financial metrics, data analysis, calculations |

## 📊 Sample Data

The project includes sample e-commerce data:

- **Orders**: 10,000 customer orders with status, totals, and metadata
- **Order Items**: Individual line items for each order
- **Payments**: Payment records with methods and status
- **Reviews**: Customer ratings and feedback

## 🔍 Key Features

### Intelligent Routing
- Automatically determines query type
- Routes to appropriate knowledge base
- Handles both qualitative and quantitative queries

### Dual Knowledge Base Support
- **Unstructured**: Document comprehension, narrative analysis
- **Structured**: SQL generation, data aggregation, metrics

### Error Handling
- Graceful fallback mechanisms
- Detailed error reporting
- Query validation

## 🧪 Testing

The notebooks include comprehensive examples:

1. **Business Strategy Query**: Tests unstructured knowledge base
2. **Financial Data Query**: Tests structured knowledge base
3. **Mixed Queries**: Demonstrates intelligent routing

## 🔒 Security

- IAM roles with least privilege access
- Secure database connections
- Encrypted data storage in S3
- Bedrock service roles for knowledge base access

## 🧹 Cleanup

To avoid AWS charges, run the cleanup sections in the notebooks:

```python
# Delete Knowledge Base and associated resources
structured_kb.delete_kb(delete_iam_roles_and_policies=True)

# Delete Redshift infrastructure
cleanup_redshift_environment()
```

## 📚 Learning Resources

- [Amazon Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [Strands Framework Documentation](https://strands.readthedocs.io/)
- [Amazon Redshift Serverless](https://docs.aws.amazon.com/redshift/latest/mgmt/working-with-serverless.html)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and enhancement requests.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Important Notes

- Monitor AWS costs while running the project
- Ensure proper cleanup of resources after testing
- Knowledge Base IDs must be updated to match your environment
- Some operations may take several minutes to complete

## 🆘 Troubleshooting

### Common Issues

1. **Knowledge Base not found**: Verify KB IDs are correct
2. **Permission errors**: Check IAM roles and policies
3. **Redshift connection issues**: Ensure workgroup is active
4. **Tool routing problems**: Verify query types match expected patterns

### Support

For questions and support:
- Check the notebook outputs for detailed error messages
- Review AWS CloudWatch logs for service-level issues
- Ensure all prerequisites are properly configured 