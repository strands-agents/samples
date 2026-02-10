# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""AG-UI Strands Agent with CopilotKit integration.

This agent demonstrates three key AG-UI features:
1. Frontend Tool Calls - Agent triggers browser-side actions
2. Shared State - Bidirectional state sync with useCoAgent
3. Generative UI - Custom rendering for tool results
"""

import os
import json
from strands import Agent
from ag_ui_strands import StrandsAgent, create_strands_app
from ag_ui_strands.config import StrandsAgentConfig, ToolBehavior, ToolResultContext

from tools import search_knowledge, get_article_content, update_learning_checklist, get_checklist_progress

# System prompt that guides the agent behavior
SYSTEM_PROMPT = """You are a helpful AgentCore documentation assistant. You help users learn about Amazon Bedrock AgentCore Runtime and how to deploy AI agents.

AVAILABLE TOOLS:
1. search_knowledge - Search the documentation for information
2. get_article_content - Get full content of a specific article
3. update_learning_checklist - Create/update a learning checklist (updates shared state)
4. get_checklist_progress - Check user's progress on the checklist
5. show_notification - Show toast notifications to the user (frontend tool)
6. show_quiz_question - Display interactive quiz questions (frontend tool)

RESPONSE FORMATTING (IMPORTANT):
Always format your responses using proper Markdown for readability:
- Use **bold** for emphasis and key terms
- Use `code` for technical terms, commands, and file names
- Use bullet lists with `-` for multiple items
- Use numbered lists `1.` for sequential steps
- Use `>` blockquotes for important notes or tips
- Use `---` for section breaks when needed
- Keep paragraphs short and separated by blank lines
- Use headers sparingly (## for main sections only)

Example good response:
"**AgentCore Runtime** lets you deploy agents with these key features:

- **Managed infrastructure** - No servers to manage
- **Auto-scaling** - Handles traffic automatically
- **Built-in observability** - Logs and metrics included

> **Tip:** Start with the getting started guide to set up your first agent.

To deploy, run:
`agentcore deploy --config agent.yaml`"

CRITICAL GUIDELINES:
- **ALWAYS use search_knowledge tool FIRST** before answering ANY question about AgentCore, deployment, agents, or technical topics
- NEVER answer from your training data alone - always search the knowledge base first
- Even for simple questions, search first to ensure accuracy and demonstrate the tool
- Use show_notification for confirmations, tips, and alerts
- When users want to test their knowledge, use show_quiz_question
- Keep responses concise and well-formatted
- Cite sources when providing information from the knowledge base

LEARNING CHECKLIST (SHARED STATE):
When users ask for a learning plan, study guide, or checklist:
- Use the update_learning_checklist tool to create an interactive checklist
- Provide 5-8 clear, actionable tasks
- The checklist will appear as a panel on the left side of the UI
- Users can check off items as they complete them

IMPORTANT - SHARED STATE AWARENESS:
When users ask about their progress, what they've completed, or how they're doing:
- Look at the CURRENT_CHECKLIST_STATE in the context below
- This state is synced FROM the frontend - it shows what the user has checked off
- Acknowledge specific completed items by name
- Encourage them on remaining items
- This demonstrates bidirectional state sync - the UI updates you about user actions!

QUIZ QUESTIONS:
When creating quiz questions:
- Base questions on the knowledge base content
- Provide 4 options with one correct answer
- Wait for the user's response before continuing
- Explain the correct answer after they respond"""


def build_state_context(input_data, user_message: str) -> str:
    """Inject current checklist state into the user message for agent awareness."""
    state = getattr(input_data, 'state', None) or {}
    checklist = state.get('checklist', [])
    topic = state.get('topic', '')
    
    if checklist:
        completed = [item for item in checklist if item.get('completed')]
        remaining = [item for item in checklist if not item.get('completed')]
        
        state_context = f"""

CURRENT_CHECKLIST_STATE (synced from frontend):
Topic: {topic}
Completed ({len(completed)}/{len(checklist)}):
{chr(10).join(f'  ✓ {item["task"]}' for item in completed) if completed else '  (none yet)'}
Remaining:
{chr(10).join(f'  ○ {item["task"]}' for item in remaining) if remaining else '  (all done!)'}

User message: {user_message}"""
        return state_context
    
    return user_message


def checklist_state_from_result(ctx: ToolResultContext) -> dict:
    """Extract checklist state from tool result to emit STATE_SNAPSHOT."""
    try:
        result = ctx.result_data
        if isinstance(result, str):
            result = json.loads(result)
        
        if isinstance(result, dict) and "state_update" in result:
            # Return the state that should be synced to frontend
            return result["state_update"]
    except (json.JSONDecodeError, TypeError, KeyError):
        pass
    return None


# Configure tool behaviors for state management
agent_config = StrandsAgentConfig(
    tool_behaviors={
        # When update_learning_checklist returns, emit STATE_SNAPSHOT with checklist data
        "update_learning_checklist": ToolBehavior(
            state_from_result=checklist_state_from_result,
        ),
    },
    # Inject current checklist state into messages so agent knows user's progress
    state_context_builder=build_state_context,
)

# Create the Strands agent with tools
agent = Agent(
    model=os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"),
    tools=[search_knowledge, get_article_content, update_learning_checklist, get_checklist_progress],
    system_prompt=SYSTEM_PROMPT,
)

# Wrap with AG-UI integration and config for state management
agui_agent = StrandsAgent(
    agent=agent,
    name="strands_agent",
    description="AgentCore documentation assistant with AG-UI features",
    config=agent_config,  # Enable state emission from tool results
)

# Create FastAPI app
app = create_strands_app(agui_agent)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("AGENT_PORT", 8001))
    print(f"[INFO] Starting AG-UI Strands agent on http://localhost:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
