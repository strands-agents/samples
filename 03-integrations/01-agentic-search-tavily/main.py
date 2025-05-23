#!/usr/bin/env python3
"""
🌐 Web Researcher Agent

A Strands agent specialized in web research using the Tavily API.

Usage:
- Set your TAVILY_API_KEY in the environment or modify the code to hardcode it.

Examples:
    "What are the latest developments in quantum computing?"
    "Find recent studies on climate change from 2022–2023, focusing on impact to coastal regions."
"""

import os
import re
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict

from dotenv import load_dotenv
from strands import Agent, tool
from tavily import TavilyClient

load_dotenv()


TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise RuntimeError("Please set the TAVILY_API_KEY environment variable.")

RESEARCH_DIR = "research_findings"
os.makedirs(RESEARCH_DIR, exist_ok=True)

# Prompt for the agent
RESEARCH_SYSTEM_PROMPT = """You are a thorough web researcher. For each question:
1. Determine what information is needed
2. Search reliable sources using Tavily
3. Verify using multiple sources
4. Extract key findings and cite sources
5. Save findings to a file with proper formatting
6. Synthesize into a clear and comprehensive answer

Prioritize academic publications, reputable news, and official documentation.
Use markdown with headings, bullet points, and citations when saving."""


@tool
@lru_cache(maxsize=32)
def tavily_search(query: str) -> Dict[str, Any]:
    """Perform a web search using Tavily API."""
    client = TavilyClient(api_key=TAVILY_API_KEY)
    response = client.search(query=query)

    if not response.get("results"):
        raise Exception("Tavily search did not provide results")

    return response.get("results")


def _generate_filename(question: str) -> str:
    """Generate a safe filename with timestamp based on the question."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_question = re.sub(r"[^\w\s-]", "", question[:40]).strip().lower()
    safe_question = re.sub(r"[-\s]+", "_", safe_question)
    return f"{RESEARCH_DIR}/{timestamp}_{safe_question}.md"


@tool
def write_md_file(filename: str, content: str) -> None:
    """Write markdown content to a file."""
    print(f"Saving research findings to {filename}...")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)


# Initialize the agent
research_agent = Agent(
    system_prompt=RESEARCH_SYSTEM_PROMPT,
    tools=[tavily_search, write_md_file],
)


def ask_research_question(question: str) -> str:
    """Ask the research agent a question and handle the file-saving logic."""
    filename = _generate_filename(question)
    message = (
        f"Research question: {question}\n\n"
        f"Save a well-structured report to: {filename}\n"
        f"Include key findings, analysis, and sources. Return the filename.\n"
        f"For simple questions, provide a brief answer directly.\n"
        f"If nothing relevant is found, inform the user."
    )
    return research_agent(message)


def run_interactive_session() -> None:
    """Run an interactive terminal session for research."""
    print("\n🌐 Web Researcher Agent 🌐\n")
    print(
        "This agent uses Tavily search to help you research topics.\n"
        "Findings are saved in the 'research_findings' directory.\n"
        "Type your question or 'exit' to quit.\n"
    )
    print(
        "Try following examples: ",
        "- What are the latest developments in quantum computing?"
        "- Find recent studies on climate change from 2022–2023, focusing on impact to coastal regions.",
    )

    while True:
        query = input("\nResearch> ").strip()
        if query.lower() == "exit":
            print(f"\nUsage metrics:\n{research_agent.event_loop_metrics}")
            print("Goodbye! 👋")
            break

        if not query:
            continue

        print("\nResearching... Please wait.\n")
        response = ask_research_question(query)
        print(response)
        print("\n✅ Research complete! You may ask another question or type 'exit'.\n")


if __name__ == "__main__":
    run_interactive_session()
