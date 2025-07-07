# Agent Orchestrator with Specialized Assistants

Build a hierarchical multi-agent system where specialized AI agents are wrapped as tools and coordinated by an orchestrator agent to handle complex, multi-domain queries.

Learn more about this pattern at Serverless Land Patterns: [Link will be generated]

**Important:** this application uses various AWS services and there are costs associated with these services after the Free Tier usage - please see the [AWS Pricing page](https://aws.amazon.com/pricing/) for details. You are responsible for any AWS costs incurred. No warranty is implied in this example.

## Requirements

* [AWS CLI](https://aws.amazon.com/cli/) installed and configured
* Python 3.10 or later
* Strands Agents SDK
* Amazon Bedrock access

## Deployment Instructions

1. Create a new directory and install dependencies
    ```bash
    mkdir agent-orchestrator && cd agent-orchestrator
    pip install strands-agents strands-agents-tools
    ```
2. Copy the source code files from this pattern
3. Run the orchestrator:
    ```bash
    python src/agent.py
    ```

## How it works

This pattern demonstrates the "Agents as Tools" architectural approach where specialized AI agents are wrapped as callable functions and coordinated by an orchestrator:

### Architecture Components

1. **Orchestrator Agent**: The main agent that handles user interaction and routes queries to appropriate specialists
2. **Research Assistant**: Specialized agent for gathering factual information and research
3. **Product Recommendation Assistant**: Expert agent for product suggestions and shopping advice
4. **Trip Planning Assistant**: Travel specialist for creating itineraries and travel advice

### Architecture Flow

```
User Query → Orchestrator Agent → Determines Appropriate Specialist → Calls Specialist Agent → Returns Response
```

### Key Benefits

- **Separation of Concerns**: Each agent has a focused area of responsibility
- **Hierarchical Delegation**: Clear chain of command with the orchestrator making routing decisions
- **Modular Architecture**: Specialists can be added, removed, or modified independently
- **Improved Performance**: Each agent has tailored system prompts optimized for specific tasks

## Testing

1. Run the orchestrator:
    ```bash
    python src/agent.py
    ```

2. Try these example queries that demonstrate routing to different specialists:
    - **Research**: "Tell me about the latest developments in quantum computing"
    - **Product Recommendations**: "I need hiking boots for winter mountaineering"
    - **Trip Planning**: "Plan a 7-day itinerary for visiting Tokyo"
    - **Multi-domain**: "Research Spain's culture and help me plan a 5-day Madrid trip"

3. Observe how the orchestrator routes queries to appropriate specialist agents

## Advanced Usage

### Sequential Agent Communication

The pattern also supports sequential agent workflows where output from one agent feeds into another:

```python
# Research first, then summarize
research_response = research_agent(query)
summary_response = summary_agent(research_response)
```

### Adding New Specialists

To add a new specialist agent:

1. Create the specialist agent with focused system prompt
2. Wrap it as a tool using the `@tool` decorator
3. Add it to the orchestrator's tools list
4. Update the orchestrator's system prompt with routing logic

## Cleanup

This pattern runs locally and doesn't create AWS resources, so no cleanup is needed. The only costs are from Amazon Bedrock API calls.

## Next Steps

Consider these enhancements:
- Add memory to maintain conversation context across agent calls
- Implement caching to avoid redundant specialist calls
- Add confidence scoring for agent selection
- Deploy as a multi-container application
- Add monitoring and observability for agent interactions
- Implement parallel agent execution for independent tasks

## Documentation
- [Strands Agents Documentation](https://strandsagents.com/)
- [Multi-Agent Systems Guide](https://strandsagents.com/latest/user-guide/concepts/multi-agent/)
- [Agents as Tools Pattern](https://strandsagents.com/latest/user-guide/concepts/multi-agent/agents-as-tools/)

## License

This project is licensed under the MIT-0 License. See the LICENSE file. 