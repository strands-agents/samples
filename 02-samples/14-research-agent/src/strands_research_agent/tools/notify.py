"""
Notification system for Strands Agent.

This module provides functionality to create and manage notifications from agents
and background tasks. Notifications can be displayed to the user, logged, and
optionally trigger system notifications.

Features:
- Send text notifications to the main agent's output
- Show system notifications (desktop/OS level)
- Customize notification priority and persistence
- Support for notification categories and filtering
- Integration with background tasks for completion alerts

Usage with Strands Agent:
```python
from strands import Agent
from strands_tools import notify, tasks

agent = Agent(tools=[notify, tasks])

# Send a simple notification
agent.tool.notify(
    message="Analysis complete!",
    title="Task Status"
)

# Send a high-priority notification with system alert
agent.tool.notify(
    message="Critical error detected in system monitoring",
    title="Alert",
    priority="high",
    show_system_notification=True
)

# Send notification from a background task
agent.tool.notify(
    message="Background research task found 5 relevant papers",
    title="Research Update",
    category="research",
    source="background_task_123"
)
```
"""

import json
import logging
import os
import platform
import re
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from strands.types.tools import ToolResult, ToolUse

logger = logging.getLogger(__name__)


# Input validation and sanitization
def _validate_and_sanitize_text(text: str, max_length: int = 1000) -> str:
    """
    Validate and sanitize text input for notifications.

    Args:
        text: Input text to validate
        max_length: Maximum allowed length

    Returns:
        Sanitized text string

    Raises:
        ValueError: If input is invalid or too long
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string")

    if not text.strip():
        raise ValueError("Input cannot be empty or whitespace only")

    if len(text) > max_length:
        raise ValueError(f"Input too long (max {max_length} characters)")

    # Remove or escape potentially dangerous characters
    # Keep only printable ASCII and basic Unicode characters
    sanitized = re.sub(r"[^\w\s\.\,\!\?\-\(\)\[\]\:\;\'\"]+", "", text)

    # Additional sanitization: remove common shell metacharacters
    dangerous_chars = ["`", "$", "\\", "|", "&", ";", ">", "<", "*", "?"]
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")

    return sanitized.strip()


def _check_command_availability(command: str) -> bool:
    """Check if a command is available on the system."""
    return shutil.which(command) is not None


TOOL_SPEC = {
    "name": "notify",
    "description": "Send notifications to the main agent and optionally trigger system notifications",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The notification message content",
                },
                "title": {
                    "type": "string",
                    "description": "Optional title for the notification",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "normal", "high"],
                    "description": "Priority level of the notification (default: normal)",
                },
                "category": {
                    "type": "string",
                    "description": "Category or type of notification for filtering/organization",
                },
                "show_system_notification": {
                    "type": "boolean",
                    "description": "Whether to also show a system notification (desktop/OS)",
                },
                "source": {
                    "type": "string",
                    "description": "Source of the notification (e.g., task ID, agent name)",
                },
                "persistent": {
                    "type": "boolean",
                    "description": "Whether this notification should be saved to history",
                },
            },
            "required": ["message"],
        }
    },
}

# Directory to store notification history
NOTIFICATIONS_DIR = Path.cwd() / "notifications"
NOTIFICATIONS_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_FILE = NOTIFICATIONS_DIR / "notification_history.jsonl"


def _show_system_notification(title, message):
    """Display a system notification using the appropriate method for the OS."""
    try:
        # Validate and sanitize inputs
        safe_title = _validate_and_sanitize_text(title, max_length=100)
        safe_message = _validate_and_sanitize_text(message, max_length=500)

        system = platform.system()

        if system == "Darwin":  # macOS
            # Use osascript to show notification with secure subprocess call
            if not _check_command_availability("osascript"):
                logger.warning("osascript not available on macOS")
                return False

            # Use array syntax to prevent command injection
            cmd = [
                "osascript",
                "-e",
                f'display notification "{safe_message}" with title "{safe_title}"',
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,  # Don't raise exception on non-zero exit
            )

            if result.returncode != 0:
                logger.error(f"osascript failed: {result.stderr}")
                return False

            return True

        elif system == "Linux":
            # Try to use notify-send if available
            if not _check_command_availability("notify-send"):
                logger.warning("notify-send not available on Linux")
                return False

            # Use array syntax to prevent command injection
            cmd = ["notify-send", safe_title, safe_message]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10, check=False
            )

            if result.returncode != 0:
                logger.error(f"notify-send failed: {result.stderr}")
                return False

            return True

        elif system == "Windows":
            # Use Windows toast notifications if available
            try:
                from win10toast import ToastNotifier

                toaster = ToastNotifier()
                # win10toast handles its own input validation and is safe
                toaster.show_toast(safe_title, safe_message, duration=5)
                return True
            except ImportError:
                # Fall back to a simpler approach using ctypes (safer than os.system)
                try:
                    import ctypes

                    # MessageBoxW is safe as it doesn't execute shell commands
                    ctypes.windll.user32.MessageBoxW(0, safe_message, safe_title, 0)
                    return True
                except Exception as e:
                    logger.error(f"Windows notification failed: {e}")
                    return False

        else:
            logger.warning(f"Unsupported operating system: {system}")
            return False

    except ValueError as e:
        logger.error(f"Invalid input for system notification: {e}")
        return False
    except subprocess.TimeoutExpired:
        logger.error("System notification command timed out")
        return False
    except Exception as e:
        logger.error(f"Failed to show system notification: {e}")
        return False


def _log_notification(notification_data):
    """Log notification to the history file securely."""
    if not notification_data.get("persistent", True):
        return

    try:
        # Validate that we're writing to the correct directory (prevent path traversal)
        history_file_path = HISTORY_FILE.resolve()
        notifications_dir_path = NOTIFICATIONS_DIR.resolve()

        # Ensure the history file is within the notifications directory
        if not str(history_file_path).startswith(str(notifications_dir_path)):
            logger.error("Security: Attempted path traversal in notification logging")
            return

        # Ensure notifications directory exists
        NOTIFICATIONS_DIR.mkdir(parents=True, exist_ok=True)

        # Add timestamp if not present
        if "timestamp" not in notification_data:
            notification_data["timestamp"] = datetime.now().isoformat()

        # Validate notification data before writing
        required_fields = ["message", "title", "priority", "category", "source"]
        for field in required_fields:
            if field not in notification_data:
                logger.warning(f"Missing required field '{field}' in notification data")
                return

            # Validate field values
            if not isinstance(notification_data[field], str):
                logger.warning(f"Invalid type for field '{field}' in notification data")
                return

        # Append to history file with proper error handling
        with open(history_file_path, "a", encoding="utf-8") as f:
            json_line = json.dumps(notification_data, ensure_ascii=False)
            f.write(json_line + "\n")

    except (IOError, OSError, json.JSONEncodeError) as e:
        logger.error(f"Failed to log notification to history file: {e}")
    except Exception as e:
        logger.error(f"Unexpected error logging notification: {e}")


def _get_notification_history(limit=None, category=None, min_priority=None):
    """Get notification history with optional filtering and security checks."""
    try:
        # Validate that we're reading from the correct file (prevent path traversal)
        history_file_path = HISTORY_FILE.resolve()
        notifications_dir_path = NOTIFICATIONS_DIR.resolve()

        # Ensure the history file is within the notifications directory
        if not str(history_file_path).startswith(str(notifications_dir_path)):
            logger.error(
                "Security: Attempted path traversal in notification history access"
            )
            return []

        if not os.path.exists(history_file_path):
            return []

        notifications = []
        priority_levels = {"low": 1, "normal": 2, "high": 3}
        min_priority_level = priority_levels.get(min_priority, 1) if min_priority else 1

        # Limit the number of lines we read to prevent memory exhaustion
        max_lines_to_read = 10000
        lines_read = 0

        with open(history_file_path, "r", encoding="utf-8") as f:
            for line in f:
                lines_read += 1
                if lines_read > max_lines_to_read:
                    logger.warning(
                        f"Stopped reading notification history after {max_lines_to_read} lines"
                    )
                    break

                try:
                    line = line.strip()
                    if not line:  # Skip empty lines
                        continue

                    notification = json.loads(line)

                    # Validate notification structure
                    if not isinstance(notification, dict):
                        continue

                    # Apply filters with validation
                    if category and notification.get("category") != category:
                        continue

                    if min_priority:
                        notification_priority = notification.get("priority", "normal")
                        if notification_priority not in priority_levels:
                            continue  # Skip invalid priority levels
                        if (
                            priority_levels.get(notification_priority, 2)
                            < min_priority_level
                        ):
                            continue

                    notifications.append(notification)

                except json.JSONDecodeError as e:
                    logger.warning(
                        f"Skipping invalid JSON line in notification history: {e}"
                    )
                    continue
                except Exception as e:
                    logger.warning(f"Error processing notification history line: {e}")
                    continue

        # Sort by timestamp (newest first) and apply limit
        notifications.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        if limit and limit > 0:
            notifications = notifications[:limit]

        return notifications

    except (IOError, OSError) as e:
        logger.error(f"Failed to read notification history: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error reading notification history: {e}")
        return []


def notify(tool: ToolUse, **kwargs: Any) -> ToolResult:
    """
    Send notifications to the main agent and optionally trigger system notifications.

    This function creates notifications that can be displayed to the user, logged
    for future reference, and optionally trigger system-level notifications.

    Args:
        tool (ToolUse): Tool use object containing the following:
            - message: The notification message content
            - title: Optional title for the notification
            - priority: Priority level (low, normal, high)
            - category: Category of notification for filtering
            - show_system_notification: Whether to show system notification
            - source: Source of the notification
            - persistent: Whether to save this notification to history
            - action: Optional action - "send" (default) or "history" to get notification history
            - limit: Limit for history retrieval (used with action="history")
            - filter_category: Category filter for history (used with action="history")
            - min_priority: Minimum priority filter for history (used with action="history")
        **kwargs (Any): Additional keyword arguments

    Returns:
        ToolResult: Dictionary containing status and response content
    """
    tool_use_id = tool["toolUseId"]
    tool_input = tool["input"]

    try:
        # Check for history action
        action = tool_input.get("action", "send")

        # Validate action parameter
        valid_actions = ["send", "history"]
        if action not in valid_actions:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [
                    {
                        "text": f"Error: Invalid action '{action}'. Must be one of: {valid_actions}"
                    }
                ],
            }

        if action == "history":
            # Return notification history
            limit = tool_input.get("limit", 10)
            category = tool_input.get("filter_category")
            min_priority = tool_input.get("min_priority")

            # Validate limit parameter
            if not isinstance(limit, int) or limit < 1 or limit > 1000:
                return {
                    "toolUseId": tool_use_id,
                    "status": "error",
                    "content": [
                        {"text": "Error: Limit must be an integer between 1 and 1000"}
                    ],
                }

            # Validate category parameter if provided
            if category is not None:
                try:
                    category = _validate_and_sanitize_text(category, max_length=50)
                except ValueError as e:
                    return {
                        "toolUseId": tool_use_id,
                        "status": "error",
                        "content": [{"text": f"Error: Invalid category filter: {e}"}],
                    }

            # Validate min_priority parameter if provided
            valid_priorities = ["low", "normal", "high"]
            if min_priority is not None and min_priority not in valid_priorities:
                return {
                    "toolUseId": tool_use_id,
                    "status": "error",
                    "content": [
                        {
                            "text": f"Error: Invalid min_priority '{min_priority}'. Must be one of: {valid_priorities}"
                        }
                    ],
                }

            notifications = _get_notification_history(limit, category, min_priority)

            if not notifications:
                return {
                    "toolUseId": tool_use_id,
                    "status": "success",
                    "content": [
                        {"text": "No notifications found matching the criteria"}
                    ],
                }

            # Format notifications for display
            result_content = [{"text": f"Recent Notifications ({len(notifications)}):"}]

            for notification in notifications:
                priority_indicators = {"low": "📢", "normal": "🔔", "high": "⚠️"}
                priority = notification.get("priority", "normal")
                indicator = priority_indicators.get(priority, "🔔")

                timestamp = notification.get("timestamp", "")
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        formatted_time = timestamp
                else:
                    formatted_time = "Unknown time"

                title = notification.get("title", "Notification")
                message = notification.get("message", "")
                source = notification.get("source", "")
                category = notification.get("category", "")

                notification_text = f"{indicator} [{formatted_time}] {title}: {message}"
                if source:
                    notification_text += f" (from: {source})"
                if category:
                    notification_text += f" [category: {category}]"

                result_content.append({"text": notification_text})

            return {
                "toolUseId": tool_use_id,
                "status": "success",
                "content": result_content,
            }

        # Normal send notification action - validate all inputs
        message = tool_input.get("message")
        if not message:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": "Error: message is required for notifications"}],
            }

        # Validate and sanitize message
        try:
            message = _validate_and_sanitize_text(message, max_length=1000)
        except ValueError as e:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": f"Error: Invalid message: {e}"}],
            }

        # Validate and sanitize title
        title = tool_input.get("title", "Notification")
        try:
            title = _validate_and_sanitize_text(title, max_length=100)
        except ValueError as e:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": f"Error: Invalid title: {e}"}],
            }

        # Validate priority
        priority = tool_input.get("priority", "normal")
        valid_priorities = ["low", "normal", "high"]
        if priority not in valid_priorities:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [
                    {
                        "text": f"Error: Invalid priority '{priority}'. Must be one of: {valid_priorities}"
                    }
                ],
            }

        # Validate and sanitize category
        category = tool_input.get("category", "general")
        try:
            category = _validate_and_sanitize_text(category, max_length=50)
        except ValueError as e:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": f"Error: Invalid category: {e}"}],
            }

        # Validate show_system_notification
        show_system_notification = tool_input.get("show_system_notification", False)
        if not isinstance(show_system_notification, bool):
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [
                    {"text": "Error: show_system_notification must be a boolean"}
                ],
            }

        # Validate and sanitize source
        source = tool_input.get("source", "agent")
        try:
            source = _validate_and_sanitize_text(source, max_length=50)
        except ValueError as e:
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": f"Error: Invalid source: {e}"}],
            }

        # Validate persistent
        persistent = tool_input.get("persistent", True)
        if not isinstance(persistent, bool):
            return {
                "toolUseId": tool_use_id,
                "status": "error",
                "content": [{"text": "Error: persistent must be a boolean"}],
            }

        # Create notification data structure
        notification_data = {
            "message": message,
            "title": title,
            "priority": priority,
            "category": category,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "persistent": persistent,
        }

        # Log notification if persistent
        if persistent:
            _log_notification(notification_data)

        # Format notification message with priority indicator
        priority_indicators = {"low": "📢", "normal": "🔔", "high": "⚠️"}
        indicator = priority_indicators.get(priority, "🔔")

        formatted_message = f"{indicator} {title}: {message}"
        if source != "agent":
            formatted_message += f" (from: {source})"

        # Show system notification if requested
        system_notification_shown = False
        if show_system_notification:
            system_notification_shown = _show_system_notification(title, message)

        # Return notification content
        result_content = [{"text": formatted_message}]

        if show_system_notification:
            status_msg = (
                "System notification displayed"
                if system_notification_shown
                else "System notification failed"
            )
            result_content.append({"text": status_msg})

        return {
            "toolUseId": tool_use_id,
            "status": "success",
            "content": result_content,
        }

    except Exception as e:
        logger.error(f"Unexpected error in notify function: {e}")
        return {
            "toolUseId": tool_use_id,
            "status": "error",
            "content": [{"text": f"Error: An unexpected error occurred: {str(e)}"}],
        }
