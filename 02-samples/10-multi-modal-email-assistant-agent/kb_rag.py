#!/usr/bin/env python3
"""
Knowledge Base RAG (Retrieval Augmented Generation) Agent

A tool for retrieving and analyzing information from Amazon Bedrock Knowledge Bases.
"""

import os
import uuid
import argparse
from typing import Dict, Any

from strands import Agent
from strands.models import BedrockModel
from strands_tools import retrieve, think

# ======== DEFAULT CONFIGURATION ========
# Default values (will be used if not provided as command-line arguments)
DEFAULT_KB_ID = "<YOUR_KB_ID>"  # Replace with your actual KB ID
DEFAULT_REGION = "us-east-1"  # Set to the region where your KB is located
DEFAULT_MIN_SCORE = 0.4
# ======================================


def retrieve_from_kb(
    query: str, kb_id: str, min_score: float, region: str
) -> Dict[str, Any]:
    """
    Retrieve information from a knowledge base based on a query.

    Args:
        query: The search query
        kb_id: Knowledge Base ID
        min_score: Minimum relevance score
        region: AWS region

    Returns:
        Dictionary containing retrieval results
    """
    # Set environment variables for the retrieve tool
    os.environ["KNOWLEDGE_BASE_ID"] = kb_id
    os.environ["MIN_SCORE"] = str(min_score)
    os.environ["AWS_REGION"] = region

    try:
        # Call the retrieve tool directly
        retrieve_response = retrieve.retrieve(
            {
                "toolUseId": str(uuid.uuid4()),
                "input": {
                    "text": query,
                    "score": min_score,
                    "numberOfResults": 5,
                    "knowledgeBaseId": kb_id,
                    "region": region,
                },
            }
        )

        return retrieve_response
    except Exception as e:
        print(f"Error details: {str(e)}")
        return {
            "status": "error",
            "message": f"Error retrieving from knowledge base: {str(e)}",
        }


def create_analyzer_agent(region: str) -> Agent:
    """
    Create an agent specialized in analyzing retrieved content.

    Args:
        region: AWS region for Bedrock

    Returns:
        Configured Phoenix Agent
    """
    return Agent(
        system_prompt="""You are a knowledgeable AI assistant. Analyze the retrieved information and provide comprehensive answers.
Focus on accuracy and clarity in your responses. When information is incomplete or uncertain, acknowledge the limitations.
Organize your response in a structured format with clear sections when appropriate.""",
        model=BedrockModel(model_id="us.amazon.nova-pro-v1:0", region=region),
        tools=[retrieve, think],
    )


def run_kb_rag(kb_id: str, min_score: float, region: str) -> None:
    """
    Run the Knowledge Base RAG application.

    Args:
        kb_id: Knowledge Base ID
        min_score: Minimum relevance score threshold
        region: AWS region for Bedrock and Knowledge Base
    """
    print(f"\n🔍 Knowledge Base Query System (Using KB: {kb_id} in region: {region})\n")

    # Create the analyzer agent
    analyzer = create_analyzer_agent(region)

    while True:
        query = input("\nQuery> ")

        if query.lower() == "exit":
            print("\nGoodbye! 👋")
            break

        print("\nSearching...\n")

        try:
            # Step 1: Retrieve information from KB
            retrieve_result = retrieve_from_kb(query, kb_id, min_score, region)

            if retrieve_result["status"] == "success":
                # Print the retrieved information
                print("Retrieved Information:")
                print("-" * 80)
                retrieved_text = retrieve_result["content"][0]["text"]
                print(retrieved_text)
                print("-" * 80)
                print("\nProcessing with AI...\n")

                # Step 2: Create message for analysis
                user_message = {
                    "role": "user",
                    "content": [
                        {
                            "text": f"""Here is the retrieved information:
{retrieved_text}

Please analyze this information and provide insights about: {query}"""
                        }
                    ],
                }

                # Add message to conversation and get response
                analyzer.messages = [user_message]
                response = analyzer(user_message["content"][0]["text"])

                # Print response
                if isinstance(response, dict) and "message" in response:
                    print("AI Analysis:")
                    print("-" * 80)
                    print(response["message"]["content"][0]["text"])
                    print("-" * 80)
                    if "metrics" in response:
                        print(
                            f"Tokens: {response['metrics'].accumulated_usage['totalTokens']}"
                        )
                else:
                    print(f"Results: {response}\n")
            else:
                print("No relevant information found in the knowledge base.")
                print(f"Response: {retrieve_result}")

                # Debug information
                print("\nDebug Information:")
                print(f"KB ID: {kb_id}")
                print(f"Region: {region}")
                print(
                    f"Environment variables: KNOWLEDGE_BASE_ID={os.environ.get('KNOWLEDGE_BASE_ID')}, AWS_REGION={os.environ.get('AWS_REGION')}"
                )

        except Exception as e:
            print(f"Error: {str(e)}\n")


def main():
    """Command line interface for the KB RAG agent."""
    parser = argparse.ArgumentParser(description="Knowledge Base RAG Agent")
    parser.add_argument(
        "--kb-id",
        type=str,
        default=DEFAULT_KB_ID,
        help=f"Knowledge Base ID (default: {DEFAULT_KB_ID})",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=DEFAULT_MIN_SCORE,
        help=f"Minimum relevance score (0-1) (default: {DEFAULT_MIN_SCORE})",
    )
    parser.add_argument(
        "--region",
        type=str,
        default=DEFAULT_REGION,
        help=f"AWS region for Bedrock and Knowledge Base (default: {DEFAULT_REGION})",
    )

    args = parser.parse_args()

    run_kb_rag(args.kb_id, args.min_score, args.region)


if __name__ == "__main__":
    main()
