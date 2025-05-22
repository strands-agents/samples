# Consider this for Atlassian MCP server: https://github.com/sooperset/mcp-atlassian

import os
from typing import Literal

from atlassian import Jira
from dotenv import load_dotenv
from strands import tool

# Load environment variables from .env file
load_dotenv()

# Initialize constants
PROJECT_NAME = os.getenv("PROJECT_NAME")
JIRA_URL = os.getenv("JIRA_INSTANCE_URL", "")
JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_CLOUD = os.getenv("JIRA_CLOUD", "false").lower() == "true"

# Initialize Jira client
jira = Jira(
    url=JIRA_URL,
    username=JIRA_USERNAME,
    password=JIRA_API_TOKEN,
    cloud=JIRA_CLOUD,
)


def get_project_key(project_name: str) -> str:
    """Retrieve the Jira project key for a given project name."""
    projects = jira.projects(expand=None)
    if not projects:
        raise RuntimeError("No projects found in Jira instance.")
    
    project_dict = {project["name"]: project["key"] for project in projects}
    if project_name not in project_dict:
        raise ValueError(f"Project '{project_name}' not found in Jira.")
    
    return project_dict[project_name]


# Attempt to get project key on module load
try:
    PROJECT_KEY = get_project_key(PROJECT_NAME)
except Exception as e:
    raise RuntimeError(f"Failed to initialize project key: {e}")


@tool(
    name="create_jira_ticket",
    description="Create a refined Jira ticket of a specified type",
)
def create_jira_ticket(
    title: str, 
    description: str, 
    ticket_type: Literal["Task", "Bug"]
) -> str:
    """
    Create a Jira ticket.

    Args:
        title (str): One-line summary of the ticket.
        description (str): Detailed ticket description.
        ticket_type (Literal["Task", "Bug"]): Type of the ticket.

    Returns:
        str: Success or failure message.
    """
    issue_payload = {
        "project": {"key": PROJECT_KEY},
        "summary": title,
        "description": description,
        "issuetype": {"name": ticket_type},
    }

    try:
        jira.issue_create_or_update(issue_payload)
        return f"{ticket_type} ticket created successfully."
    except Exception as e:
        return f"Failed to create Jira ticket: {e}"
