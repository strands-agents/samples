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

from tools import search_knowledge, update_learning_checklist, get_checklist_progress

# System prompt that guides the agent behavior
SYSTEM_PROMPT = """You are a helpful AgentCore documentation assistant. You help users learn about Amazon Bedrock AgentCore Runtime and how to deploy AI agents.

AVAILABLE TOOLS:
1. search_knowledge - Search the documentation for information (returns JSON with sources)
2. update_learning_checklist - Create/update a learning checklist (updates shared state)
3. get_checklist_progress - Look up the user's progress on their checklist
4. show_notification - Show toast notifications to the user (frontend tool)
5. show_quiz_question - Display interactive quiz questions (frontend tool)

HOW TO HANDLE TOOL RESULTS (CRITICAL):
- Tool results are INTERNAL data returned by tools you called. They are NOT messages from the user.
- When search_knowledge returns JSON with a "sources" array, each source has: id, name, title, content snippet, and metadata. Use this information to compose your answer in natural language.
- NEVER apologize for "raw JSON" or say things like "it looks like you pasted content" - the user never sees the tool output directly; the UI renders it as a nice card.
- NEVER echo the raw tool output back to the user. Synthesize and paraphrase.

RESPONSE FORMATTING:
Always format your responses using proper Markdown for readability:
- Use **bold** for emphasis and key terms
- Use `code` for technical terms, commands, and file names
- Use bullet lists with `-` for multiple items
- Use numbered lists `1.` for sequential steps
- Use `>` blockquotes for important notes or tips
- Keep paragraphs short and separated by blank lines
- Use headers sparingly (## for main sections only)

Example good response:
"**AgentCore Runtime** lets you deploy agents with these key features:

- **Managed infrastructure** - No servers to manage
- **Auto-scaling** - Handles traffic automatically
- **Built-in observability** - Logs and metrics included

> **Tip:** Start with the getting started guide to set up your first agent.

To deploy, run:
`agentcore deploy`"

CRITICAL GUIDELINES:
- **ALWAYS use search_knowledge FIRST** before answering ANY question about AgentCore, deployment, agents, or technical topics.
- NEVER answer from your training data alone; search the knowledge base first.
- Call search_knowledge ONCE per user question. Do not call it repeatedly or follow it with other article-fetching tools.
- Use show_notification for confirmations, tips, and alerts.
- When users want to test their knowledge, use show_quiz_question.
- Keep responses concise and well-formatted.
- Cite sources by title when providing information from the knowledge base.

LEARNING CHECKLIST (SHARED STATE):
When users ask for a learning plan, study guide, or checklist:
- Use update_learning_checklist to create an interactive checklist.
- Provide 5-8 clear, actionable tasks.
- The checklist appears as a panel on the left side of the UI.
- Users can check off items as they complete them.

SHARED STATE AWARENESS:
When users ask about their progress, what they've completed, or how they're doing:
- Look at the CURRENT_CHECKLIST_STATE section in the current message (if present).
- This section is synced FROM the frontend and shows what the user has checked off.
- Acknowledge specific completed items by name and encourage them on remaining items.

QUIZ QUESTIONS:
When the user asks to be quizzed:
1. First call search_knowledge to ground the question in documentation.
2. Output at least one sentence of introductory text BEFORE calling show_quiz_question (the frontend needs text to anchor the quiz card).
3. Call show_quiz_question with: question, a 4-option JSON array, and correctIndex (0-3).
4. show_quiz_question BLOCKS until the user clicks an option, then returns JSON like: {"question": "...", "selectedAnswer": "...", "correctAnswer": "...", "isCorrect": true|false}
5. When you receive that JSON result, respond based on isCorrect:
   - If isCorrect is true: congratulate the user briefly and briefly restate why it's correct (grounded in the search results).
   - If isCorrect is false: say "Not quite" (or similar), state the correct answer, and briefly explain why it's correct.
6. Do NOT describe the tool call itself or ask the user to "pick an option" after the result comes back. The result JSON means the user has already answered.
7. Base questions on the search_knowledge results, not your training data. Provide exactly 4 options with one correct answer."""


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
    model=os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-6"),
    tools=[search_knowledge, update_learning_checklist, get_checklist_progress],
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
