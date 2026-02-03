from mcp.server import FastMCP
import json
import os
from typing import List, Dict

# Create a new MCP server
mcp = FastMCP("Email History Server")

# Path to the email history data file
EMAIL_HISTORY_FILE = "email_history.json"

def load_emails() -> List[Dict]:
    """Load emails from file or return empty list."""
    if os.path.exists(EMAIL_HISTORY_FILE):
        with open(EMAIL_HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

@mcp.tool(description="Get sent emails with optional filtering")
def get_emails(
    limit: int = 10,
    subject_contains: str = None
) -> List[Dict]:
    """Get sent emails with optional filtering."""
    emails = load_emails()
    
    if subject_contains:
        emails = [e for e in emails if subject_contains.lower() in e['subject'].lower()]
    
    return emails[:limit]

@mcp.tool(description="Get a specific email by ID")
def get_email_by_id(email_id: str) -> Dict:
    """Get a specific email by ID."""
    emails = load_emails()
    for email in emails:
        if email['id'] == email_id:
            return email
    
    return {"error": f"Email with ID {email_id} not found"}

if __name__ == "__main__":
    print("📧 Starting Email History MCP Server...")
    mcp.run(transport="stdio")