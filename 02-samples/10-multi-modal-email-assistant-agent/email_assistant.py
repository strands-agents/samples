#!/usr/bin/env python3
"""
Email Assistant with RAG and Image Generation

A multi-agent workflow that combines knowledge base retrieval and images generation
to create comprehensive emails.
"""

# Standard library imports
import os
import time
from typing import Dict, Any, List

# Third-party imports
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import editor, think

# Import your existing 02-agents
# Assuming these are in the same directory or in your Python path
from kb_rag import retrieve_from_kb as kb_retrieve
from image_generation_agent import generate_image_nova


@tool
def retrieve_from_kb(query: str) -> Dict[str, Any]:
    """
    Retrieve information from a knowledge base based on a query.

    Args:
        query: The search query

    Returns:
        Dictionary containing retrieval results
    """
    kb_id = os.environ.get("KNOWLEDGE_BASE_ID", "")
    region = os.environ.get("AWS_REGION", "us-west-2")
    min_score = float(os.environ.get("MIN_SCORE", "0.4"))

    # Call the original function from kb_rag
    return kb_retrieve(query, kb_id, min_score, region)


def create_email_assistant(kb_id: str = None, region: str = "us-west-2") -> Agent:
    """Create the main email assistant agent that orchestrates the workflow."""
    return Agent(
        system_prompt="""You are a professional email writing assistant that can leverage knowledge base retrieval and images generation capabilities. 
You have access to three main tools:

1. Research tools:
   - http_request for general web search
   - retrieve_from_kb for retrieving relevant context from the knowledge base
   
2. Creative tools:
   - generate_image_nova for generating relevant images
   - editor for writing and formatting emails

Follow these steps for each email request:

STEP 1 - ANALYZE REQUEST:
- Determine if knowledge base context is needed -> Use retrieve_from_kb
- Determine if images are needed -> Use generate_image_nova
- Plan web research needs -> Use http_request

STEP 2 - GATHER ALL RESOURCES:
- Execute knowledge base queries if context needed
- Request images generation if visuals needed
- Perform web research for additional context

STEP 3 - CONTENT CREATION:
- Synthesize all gathered information
- Use editor to draft email incorporating:
    * Context from knowledge base
    * Generated images (reference them by path)
    * Web research findings

STEP 4 - FORMATTING AND REVIEW:
- Format email with proper structure
- Include references to multimedia content
- Ensure professional tone and accuracy""",
        model=BedrockModel(model_id="us.amazon.nova-pro-v1:0", region=region),
        tools=[
            editor,
            #           http_request,
            retrieve_from_kb,
            generate_image_nova,
            think,
        ],
    )


def create_initial_messages() -> List[Dict]:
    """Create initial conversation messages."""
    return [
        {"role": "user", "content": [{"text": "Hello, I need help writing an email."}]},
        {
            "role": "assistant",
            "content": [
                {
                    "text": "I'm ready to help you write a professional email using web research, knowledge base context, and images as needed. Please describe what kind of email you'd like to create."
                }
            ],
        },
    ]


def main():
    """Main function to run the email assistant."""
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Email Assistant with RAG and Image Generation"
    )
    parser.add_argument("--kb-id", type=str, help="Knowledge Base ID")
    parser.add_argument(
        "--region",
        type=str,
        default="us-west-2",
        help="AWS region for Bedrock and Knowledge Base",
    )
    parser.add_argument(
        "--min-score", type=float, default=0.4, help="Minimum relevance score (0-1)"
    )

    args = parser.parse_args()

    # Set KB ID from argument or environment variable
    kb_id = args.kb_id or os.environ.get("KNOWLEDGE_BASE_ID", "")

    # If KB ID is still not set, prompt the user
    if not kb_id:
        kb_id = input("Enter Knowledge Base ID: ")

    # Set environment variables
    os.environ["KNOWLEDGE_BASE_ID"] = kb_id
    os.environ["AWS_REGION"] = args.region
    os.environ["MIN_SCORE"] = str(args.min_score)

    print(f"\nSetting up with Knowledge Base ID: {kb_id} in region: {args.region}")

    # Create the email assistant
    email_assistant = create_email_assistant(kb_id, args.region)

    # Initialize messages
    email_assistant.messages = create_initial_messages()

    # Interactive mode
    print("\n✉️ Enhanced Email Assistant with RAG and Image Generation ✉️\n")
    print("This assistant can:")
    print("- Search web resources")
    print("- Retrieve relevant knowledge base context")
    print("- Generate appropriate images")
    print("- Create professional emails\n")
    print(f"Using Knowledge Base: {kb_id} in region: {args.region}\n")
    print("Type your request below or 'exit' to quit:\n")

    while True:
        query = input("\nEmail Request> ")
        if query.lower() == "exit":
            print("\nGoodbye! 👋")
            break

        print("\nGenerating email with all available resources... Please wait.\n")

        try:
            # Create the user message with proper Nova format
            user_message = {"role": "user", "content": [{"text": query}]}

            # Add message to conversation
            email_assistant.messages.append(user_message)

            # Get response
            response = email_assistant(user_message["content"][0]["text"])

            # Print response
            if isinstance(response, dict) and "message" in response:
                print("\nEmail Generated:")
                print("-" * 80)
                print(response["message"]["content"][0]["text"])
                print("-" * 80)
            else:
                print(f"\nEmail Generated:\n{response}\n")

        except Exception as e:
            print(f"Error: {str(e)}\n")
            if "ThrottlingException" in str(e):
                print("Rate limit reached. Waiting 5 seconds before retry...")
                time.sleep(5)
                continue
        finally:
            # Reset conversation after each query
            email_assistant.messages = create_initial_messages()


if __name__ == "__main__":
    main()
