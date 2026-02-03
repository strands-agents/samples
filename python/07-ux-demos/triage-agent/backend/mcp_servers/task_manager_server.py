from mcp.server import FastMCP
from typing import List, Dict
import json
import os

# Simple in-memory task storage (in production, use a proper database)
TASKS_FILE = "tasks.json"

def load_tasks() -> List[Dict]:
    """Load tasks from file or return empty list."""
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_tasks(tasks: List[Dict]) -> None:
    """Save tasks to file."""
    with open(TASKS_FILE, 'w') as f:
        json.dump(tasks, f, indent=2)

# Create the MCP server
mcp = FastMCP("Task Manager Server")

@mcp.tool(description="Add a new task to the task list")
def add_task(task_description: str, priority: str = "medium") -> str:
    """Add a new task with optional priority (low, medium, high)."""
    tasks = load_tasks()
    task_id = len(tasks) + 1
    
    new_task = {
        "id": task_id,
        "description": task_description,
        "priority": priority,
        "completed": False
    }
    
    tasks.append(new_task)
    save_tasks(tasks)
    
    return f"Task '{task_description}' added with ID {task_id} and priority '{priority}'"

@mcp.tool(description="List all tasks")
def list_tasks() -> str:
    """List all tasks with their status."""
    tasks = load_tasks()
    
    if not tasks:
        return "No tasks found."
    
    result = "Current Tasks:\n"
    for task in tasks:
        status = "✅" if task["completed"] else "⏳"
        result += f"{status} ID {task['id']}: {task['description']} (Priority: {task['priority']})\n"
    
    return result

@mcp.tool(description="Mark a task as completed")
def complete_task(task_id: int) -> str:
    """Mark a task as completed by its ID."""
    tasks = load_tasks()
    
    for task in tasks:
        if task["id"] == task_id:
            task["completed"] = True
            save_tasks(tasks)
            return f"Task '{task['description']}' marked as completed!"
    
    return f"Task with ID {task_id} not found."

@mcp.tool(description="Delete a task from the list")
def delete_task(task_id: int) -> str:
    """Delete a task by its ID."""
    tasks = load_tasks()
    
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            deleted_task = tasks.pop(i)
            save_tasks(tasks)
            return f"Task '{deleted_task['description']}' deleted successfully!"
    
    return f"Task with ID {task_id} not found."

if __name__ == "__main__":
    print("📋 Starting Task Manager MCP Server...")
    print("Available at: http://localhost:8001/mcp/")
    mcp.run(transport="streamable-http", port=8001) 