# Web Search Agent with DuckDuckGo

Build a conversational AI agent that can search the web in real-time using DuckDuckGo to provide up-to-date information on any topic.

Learn more about this pattern at Serverless Land Patterns: [Link will be generated]

**Important:** this application uses various AWS services and there are costs associated with these services after the Free Tier usage - please see the [AWS Pricing page](https://aws.amazon.com/pricing/) for details. You are responsible for any AWS costs incurred. No warranty is implied in this example.

## Requirements

* [AWS CLI](https://aws.amazon.com/cli/) installed and configured
* Python 3.10 or later
* Strands Agents SDK
* DuckDuckGo Search library

## Deployment Instructions

1. Create a new directory and install dependencies
    ```bash
    mkdir websearch-agent && cd websearch-agent
    pip install strands-agents strands-agents-tools duckduckgo-search
    ```
2. Copy the source code files from this pattern
3. Run the agent:
    ```bash
    python src/agent.py
    ```

## How it works

This pattern demonstrates how to create a Strands agent with real-time web search capabilities:

1. **Custom Tool Creation**: A `websearch` tool is created using the `@tool` decorator that wraps DuckDuckGo's search API
2. **Agent Configuration**: The agent is configured with a system prompt that instructs it when and how to use web search
3. **Interactive Loop**: The agent runs in an interactive mode, allowing users to ask questions that require current information
4. **Error Handling**: The search tool includes proper error handling for rate limits and search exceptions

### Architecture

```
User Input → Strands Agent → Web Search Tool → DuckDuckGo API → Search Results → Agent Response
```

The agent uses the following components:
- **Strands Agent**: Orchestrates the conversation and decides when to search
- **Web Search Tool**: Custom tool that performs web searches
- **DuckDuckGo Search**: External API for retrieving current web information
- **Amazon Bedrock**: LLM for understanding queries and formatting responses

## Testing

1. Run the agent:
    ```bash
    python src/agent.py
    ```

2. Try these example queries:
    - "What's the latest news about AI?"
    - "Find me a recipe for chocolate chip cookies"
    - "What's the weather like in Tokyo today?"
    - "Tell me about the latest developments in quantum computing"

3. Type 'exit' to quit the application

## Cleanup

This pattern runs locally and doesn't create AWS resources, so no cleanup is needed. The only costs are from Amazon Bedrock API calls.

## Next Steps

Consider these enhancements:
- Add multiple search engines (Bing, Google)
- Implement search result caching to reduce API calls
- Add content filtering and safety checks
- Deploy as a Lambda function for serverless operation
- Add memory to maintain conversation context
- Integrate with knowledge bases for hybrid search

## Documentation
- [Strands Agents Documentation](https://strandsagents.com/)
- [DuckDuckGo Search Library](https://github.com/deedy5/duckduckgo_search)
- [Custom Tools Guide](https://strandsagents.com/latest/user-guide/concepts/tools/custom-tools/)

## License

This project is licensed under the MIT-0 License. See the LICENSE file. 