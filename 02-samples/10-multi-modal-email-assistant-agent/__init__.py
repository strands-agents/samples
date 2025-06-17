"""
Email Assistant with RAG and Image Generation

A multi-agent workflow that combines knowledge base retrieval and images generation
to create comprehensive emails.
"""

# Import main components from the email assistant
from .email_assistant import (
    create_email_assistant,
    create_initial_messages,
    main as run_email_assistant,
)

# Re-export components from kb_rag
from kb_rag import retrieve_from_kb, create_analyzer_agent, run_kb_rag

# Re-export components from image_generation_agent
from image_generation_agent import (
    generate_image_nova,
    create_image_agent,
    run_image_agent,
)

__all__ = [
    # Email assistant components
    "create_email_assistant",
    "create_initial_messages",
    "run_email_assistant",
    # KB RAG components
    "retrieve_from_kb",
    "create_analyzer_agent",
    "run_kb_rag",
    # Image generation components
    "generate_image_nova",
    "create_image_agent",
    "run_image_agent",
]
