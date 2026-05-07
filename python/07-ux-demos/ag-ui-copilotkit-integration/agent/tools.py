# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Agent tools for knowledge search and quiz generation."""

import os
import json
import re
import uuid
from pathlib import Path
from strands import tool


def get_knowledge_dir() -> Path:
    """Get the knowledge directory path."""
    return Path(__file__).parent / "knowledge"


def search_markdown_files(query: str) -> list[dict]:
    """Simple text search across markdown files."""
    knowledge_dir = get_knowledge_dir()
    results = []
    query_lower = query.lower()
    query_terms = query_lower.split()
    
    for md_file in knowledge_dir.glob("*.md"):
        content = md_file.read_text()
        content_lower = content.lower()
        
        # Calculate relevance score based on term matches
        score = 0
        for term in query_terms:
            score += content_lower.count(term)
        
        if score > 0:
            # Extract relevant sections (paragraphs containing query terms)
            paragraphs = content.split("\n\n")
            relevant_sections = []
            for para in paragraphs:
                if any(term in para.lower() for term in query_terms):
                    relevant_sections.append(para.strip())
            
            results.append({
                "filename": md_file.name,
                "title": md_file.stem.replace("-", " ").title(),
                "content": "\n\n".join(relevant_sections[:3]) if relevant_sections else content[:500],
                "score": score / len(query_terms),  # Normalize score
                "full_content": content,
            })
    
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:5]  # Return top 5


@tool
def search_knowledge(query: str) -> str:
    """Search the knowledge base for information about AgentCore.
    
    Args:
        query: The search query to find relevant documentation.
        
    Returns:
        JSON string with search results including sources and content.
    """
    results = search_markdown_files(query)
    
    if not results:
        return json.dumps({"sources": []})
    
    structured_sources = []
    for i, result in enumerate(results[:3], 1):  # Top 3 only
        # Extract section headers from full content
        headers = re.findall(r'^##?\s+(.+)$', result["full_content"], re.MULTILINE)
        structured_sources.append({
            "id": f"source_{i}",
            "name": result["filename"],
            "title": result["title"],
            "type": "document",
            "content": result["content"][:200],  # Short snippet
            "metadata": {
                "score": round(result["score"], 2),
                "sections": headers[:5],
            },
        })
    
    return json.dumps({"sources": structured_sources})


@tool
def get_article_content(filename: str) -> str:
    """Get the full content of a specific knowledge base article.
    
    Args:
        filename: The filename of the article (e.g., 'getting-started.md')
        
    Returns:
        The full markdown content of the article.
    """
    knowledge_dir = get_knowledge_dir()
    file_path = knowledge_dir / filename
    
    if not file_path.exists():
        return f"Article '{filename}' not found. Available articles: {', '.join(f.name for f in knowledge_dir.glob('*.md'))}"
    
    return file_path.read_text()



@tool
def update_learning_checklist(topic: str, tasks: list[str]) -> str:
    """Update the shared learning checklist state with new tasks.
    
    This tool updates the frontend's shared state with a learning checklist.
    The frontend will display this as an interactive checklist panel.
    
    Args:
        topic: The learning topic (e.g., "AgentCore Deployment")
        tasks: List of task descriptions for the checklist
        
    Returns:
        Confirmation message with the checklist details.
    """
    # Create checklist items with unique IDs
    checklist_items = [
        {"id": str(uuid.uuid4()), "task": task, "completed": False}
        for task in tasks
    ]
    
    # Return the state update - ag-ui-strands will emit STATE_SNAPSHOT
    # The frontend's useCoAgent hook will receive this state
    return json.dumps({
        "state_update": {
            "checklist": checklist_items,
            "topic": topic
        },
        "message": f"Created learning checklist for '{topic}' with {len(tasks)} tasks."
    })


@tool
def get_checklist_progress() -> str:
    """Look up the user's current learning checklist progress.
    
    The actual checklist items and completion status are injected into
    the conversation context from the frontend via shared state. This tool
    simply signals to the agent that it should reference the
    CURRENT_CHECKLIST_STATE section of the current message when answering.
    
    Returns:
        A short instruction pointing the agent at the shared-state context.
    """
    return "Refer to the CURRENT_CHECKLIST_STATE section of the current message for live checklist items and completion status."
