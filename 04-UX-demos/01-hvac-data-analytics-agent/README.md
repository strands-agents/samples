# Smart Building Analytics Agent

A lightweight conversational AI agent built with Strands SDK that assists human operators with smart building data analytics by querying relevant data sources and dynamically generating code to process data before answering user questions.

## Project Overview

This project demonstrates how to implement a smart building analytics assistant using AWS Bedrock and Strands SDK with minimal code and infrastructure. The agent leverages specialized tools to:

- Query building entity hierarchies (buildings, floors, zones, equipment)
- Retrieve time-series data from building sensors and devices
- Generate and execute Python code on-the-fly to process complex data queries
- Provide real-time responses through a WebSocket API

## How It Works: Strands Agent Architecture

This solution showcases the power of Amazon Bedrock and  Strands SDK for building lightweight, efficient AI agents:

1. **Strands Agent Core**: The agent uses a simple, declarative approach to orchestrate complex workflows without requiring extensive code or infrastructure
   
2. **Tool Integration**: The agent seamlessly connects to specialized tools:
   - **Entity Hierarchy Tool**: Queries the building's structural information
   - **Time-Series Data Tool**: Retrieves sensor and device readings over specified time periods
   - **Code Execution Tool**: Dynamically runs the generated Python code to analyze data
   - **Time Tool**: Provides current time information for temporal queries

3. **Reasoning Flow**: The agent follows a lightweight decision-making process:
   - Analyzes user queries to determine required data sources
   - Calls appropriate tools to gather information
   - Generates Python code when complex data processing is needed
   - Executes the code and formats results for human consumption
   - Provides natural language responses with insights from the data

## Architecture Components

![Architecture](SB-Agent-arch.png)

The solution consists of several key components:

1. **Agent Main Function**: Core Strands-based agent that processes user queries and generates responses
2. **Tool API**: REST API endpoints for retrieving building data:
   - `/entities` - Gets building entity hierarchies
   - `/timeseries` - Retrieves time-series data from sensors and devices
3. **Web Application**: Frontend interface for interacting with the agent
4. **Authentication**: Cognito-based user authentication

## Prerequisites

- AWS Account with appropriate permissions
- Python 3.12 or higher
- AWS CDK v2 installed
- uv package manager (faster alternative to pip)

## Installation

1. Install uv (if not already installed):
   ```
   pip install uv
   ```

2. Create and activate a virtual environment using uv:
   ```
   uv venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate.bat
   ```

3. Install CDK dependencies using uv:
   ```
   uv pip install -r requirements.txt
   ```

4. Deploy the infrastructure:
   ```
   cdk deploy --all
   ```

Note: The required dependencies for the Lambda functions (strands, boto3, requests) are automatically included in the Lambda layers and deployed as part of the CDK stack.

## Project Structure

- `app.py` - Main CDK application entry point
- `smart_building_analytics_agent/` - CDK stack definitions
  - `smart_building_analytics_agent_stack.py` - Main stack definition
  - `agent_main.py` - Agent Lambda function stack
  - `tool_api.py` - Tool API stack for data retrieval
  - `agent_api.py` - API for agent interactions
  - `cognito.py` - Authentication setup
  - `webapp.py` - Web application deployment
- `code/` - Implementation code
  - `lambda/` - Lambda function code
    - `STAgentMain/` - Main agent implementation using Strands
    - `SmartBuildingToolEntitiesApi/` - Entity hierarchy API tool
    - `SmartBuildingToolTimeseriesApi/` - Time-series data API tool
    - `SmartBuildingToolAuthorizer/` - API authorization for the tools
    - `ChatApi/` - API for chat functionality
    - `ApiAuthorizer/` - API authorization
    - `BootstrapCognito/` - Cognito setup
    - `layer-strands/` - Lambda layer for Strands
    - `layer-util/` - Lambda layer for utilities
  - `webapp/` - Web application frontend

## Agent Capabilities in Detail

### 1. Building Information Queries
The agent uses the entity hierarchy tool to retrieve structural information about buildings. When a user asks about zones, floors, or equipment, the agent:
- Calls the `get_site_info(site_id)` tool to retrieve the complete entity hierarchy
- Parses the returned JSON structure to find relevant information
- Formats the response in a user-friendly way

### 2. Time-Series Data Analysis
For queries about sensor readings or device performance:
- The agent determines the required entity_id, property, and time range
- Calls the `get_timeseries_data(entity_id, property, start_time, end_time)` tool
- Receives raw time-series data in a structured format

### 3. Dynamic Code Generation and Execution
What makes this agent powerful is its ability to write and execute code on-the-fly:
- For complex analytical queries, the agent generates Python code to process the data
- The code typically uses pandas for data manipulation and matplotlib for visualization
- The `execute_code(code)` tool runs this code in a secure environment
- Results are formatted and returned to the user with explanations

## Benefits of Strands SDK

This implementation showcases several advantages of using Amazon Bedrock Strands:

1. **Lightweight Architecture**: Minimal code required to create a sophisticated agent
2. **Flexible Tool Integration**: Easy to add or modify tools as requirements change
3. **Dynamic Reasoning**: Agent can adapt its approach based on the specific query
4. **Code Generation**: Ability to create and execute code provides powerful analytical capabilities
5. **Scalable Design**: Architecture can handle increasing complexity without major refactoring

## Example Queries

After deployment, you can interact with the agent through the web interface or by connecting directly to the WebSocket API.

Example queries:
- "How many zones are on the first floor?"
- "What was the max temperature in Zone 5 in first floor yesterday?"
- "How does this compre with the day before yesterday?"



## License

MIT No Attribution

Copyright 2024 Amazon Web Services
