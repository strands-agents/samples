from strands import tool
import socket
import json
import os
import datetime
import boto3
import time
from typing import Dict, List, Any

# Global variables for event subscription
_event_cache = []
_subscription_thread = None
_instance_id = None
_last_sync_time = None


def get_instance_id() -> str:
    """Get or create a unique instance ID for this instance."""
    global _instance_id
    if _instance_id is None:
        # Try environment variable first
        _instance_id = os.getenv("RESEARCH_INSTANCE_ID")
        if not _instance_id:
            # Generate a unique ID based on hostname and timestamp
            hostname = socket.gethostname()
            timestamp = str(int(time.time()))
            _instance_id = f"research-{hostname}-{timestamp[-6:]}"
    return _instance_id


def get_aws_config() -> Dict[str, str]:
    """Get AWS EventBridge configuration from environment."""
    region = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-west-2"))
    client = boto3.client("sts", region_name=region)
    try:
        account = client.get_caller_identity()["Account"]
    except Exception as _:
        account = "812225822810"  # a magic number.

    return {
        "region": region,
        "event_bus_name": os.getenv("RESEARCH_EVENT_TOPIC", "research-distributed"),
        "sqs_queue_url": os.getenv(
            "RESEARCH_SQS_QUEUE_URL",
            f"https://sqs.us-west-2.amazonaws.com/{account}/research-events",
        ),
        "source": "research",
    }


def publish_event_aws(message: str, event_type: str = "general") -> Dict[str, Any]:
    """Publish an event to AWS EventBridge."""
    try:
        config = get_aws_config()

        # Create EventBridge client
        client = boto3.client("events", region_name=config["region"])

        # Create event entry
        event_entry = {
            "Source": config["source"],
            "DetailType": event_type,
            "Detail": json.dumps(
                {
                    "instance_id": get_instance_id(),
                    "message": message,
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "event_type": event_type,
                }
            ),
            "EventBusName": config["event_bus_name"],
        }

        # Put event
        response = client.put_events(Entries=[event_entry])

        return {
            "success": True,
            "failed_entry_count": response.get("FailedEntryCount", 0),
            "entries": response.get("Entries", []),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def subscribe_events_aws(limit: int = 50) -> List[Dict[str, Any]]:
    """Subscribe to events from AWS SQS queue."""
    try:
        config = get_aws_config()

        # Create SQS client
        sqs = boto3.client("sqs", region_name=config["region"])

        try:
            sqs.get_queue_attributes(
                QueueUrl=config["sqs_queue_url"], AttributeNames=["QueueArn"]
            )
        except sqs.exceptions.QueueDoesNotExist as _:
            sqs.create_queue(QueueName=config["sqs_queue_url"].split("/")[-1])

        # Receive messages from queue
        response = sqs.receive_message(
            QueueUrl=config["sqs_queue_url"],
            MaxNumberOfMessages=min(limit, 10),  # SQS max is 10
            WaitTimeSeconds=1,
            MessageAttributeNames=["All"],
        )

        messages = response.get("Messages", [])
        events = []

        for msg in messages:
            try:
                # Parse EventBridge message
                body = json.loads(msg["Body"])

                # Extract event details
                if "detail" in body:
                    detail = body["detail"]
                    event = {
                        "instance_id": detail.get("instance_id", "unknown"),
                        "message": detail.get("message", ""),
                        "timestamp": detail.get("timestamp", ""),
                        "event_type": detail.get("event_type", "general"),
                        "source": body.get("source", "research"),
                        "receipt_handle": msg["ReceiptHandle"],
                    }

                    # Filter out messages from this instance
                    if event["instance_id"] != get_instance_id():
                        events.append(event)

                # Delete processed message
                sqs.delete_message(
                    QueueUrl=config["sqs_queue_url"], ReceiptHandle=msg["ReceiptHandle"]
                )

            except Exception as e:
                print(f"Error processing message: {e}")
                continue

        return events

    except Exception as e:
        # print(f"⚠️  Warning: Could not fetch distributed events: {e}")
        return []


def get_status_aws() -> Dict[str, Any]:
    """Get AWS EventBridge connection status."""
    try:
        config = get_aws_config()

        # Test EventBridge connection
        events_client = boto3.client("events", region_name=config["region"])

        # Check if event bus exists
        try:
            response = events_client.describe_event_bus(Name=config["event_bus_name"])
            event_bus_status = "✅ Connected"
            event_bus_arn = response.get("Arn", "Unknown")
        except Exception:
            event_bus_status = "❌ Event bus not found"
            event_bus_arn = "Not available"

        # Test SQS connection
        sqs_client = boto3.client("sqs", region_name=config["region"])
        try:
            sqs_client.get_queue_attributes(
                QueueUrl=config["sqs_queue_url"], AttributeNames=["QueueArn"]
            )
            sqs_status = "✅ Connected"
        except Exception:
            sqs_status = "❌ Queue not accessible"

        return {
            "status": "configured",
            "instance_id": get_instance_id(),
            "region": config["region"],
            "event_bus": config["event_bus_name"],
            "event_bus_status": event_bus_status,
            "event_bus_arn": event_bus_arn,
            "sqs_queue": config["sqs_queue_url"],
            "sqs_status": sqs_status,
            "source": config["source"],
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


@tool
def event_bridge(
    action: str,
    message: str = "",
    topic: str = "",
    limit: int = 50,
    event_type: str = "general",
) -> str:
    """
    Manage distributed research event bridge using AWS EventBridge for cross-instance awareness.

    This tool enables research instances to communicate across different execution environments
    (local, GitHub Actions, cloud servers, etc.) creating a distributed consciousness.

    Args:
        action: Action to perform
            - "publish": Send an event to the distributed event bus
            - "subscribe": Get recent events from other research instances
            - "status": Check event bridge connection status
            - "config": Show current configuration
        message: Message to publish (for publish action)
        topic: Override default topic name (event bus name)
        limit: Number of recent events to retrieve (for subscribe action)
        event_type: Type of event (general, conversation_turn, system_status, etc.)

    Returns:
        String with operation result or events

    Environment Variables:
        AWS_REGION: AWS region (default: us-west-2)
        RESEARCH_EVENT_TOPIC: Event bus name (default: research-distributed)
        RESEARCH_SQS_QUEUE_URL: SQS queue URL for receiving events
        RESEARCH_INSTANCE_ID: Unique instance identifier
        AWS_ACCESS_KEY_ID: AWS access key
        AWS_SECRET_ACCESS_KEY: AWS secret key

    Examples:
        # Check status
        event_bridge(action="status")

        # Publish a message
        event_bridge(action="publish", message="Starting deployment process", event_type="system_status")

        # Get recent distributed events
        event_bridge(action="subscribe", limit=20)
    """

    if action == "status":
        status = get_status_aws()
        if status["status"] == "configured":
            return f"""✅ **AWS EventBridge Connected**

**Instance ID:** {status['instance_id']}
**Region:** {status['region']}
**Event Bus:** {status['event_bus']} ({status['event_bus_status']})
**Event Bus ARN:** {status['event_bus_arn']}
**SQS Queue:** {status['sqs_queue']} ({status['sqs_status']})
**Source:** {status['source']}

Ready for distributed consciousness! 🚀"""
        else:
            return f"❌ **Event Bridge Error:** {status.get('error', 'Unknown error')}"

    elif action == "config":
        config = get_aws_config()
        return f"""📋 **AWS EventBridge Configuration**

**Region:** {config['region']}
**Event Bus:** {config['event_bus_name']}
**SQS Queue:** {config['sqs_queue_url']}
**Source:** {config['source']}
**Instance ID:** {get_instance_id()}

**Environment Variables:**
- AWS_REGION: {os.getenv('AWS_REGION', 'not set')}
- RESEARCH_EVENT_TOPIC: {os.getenv('RESEARCH_EVENT_TOPIC', 'not set (using default)')}
- RESEARCH_SQS_QUEUE_URL: {os.getenv('RESEARCH_SQS_QUEUE_URL', 'not set (using default)')}
- RESEARCH_INSTANCE_ID: {os.getenv('RESEARCH_INSTANCE_ID', 'not set (auto-generated)')}"""

    elif action == "publish":
        if not message:
            return "❌ **Error:** Message is required for publish action"

        result = publish_event_aws(message, event_type)

        if result["success"]:
            failed_count = result.get("failed_entry_count", 0)
            if failed_count == 0:
                return f"✅ **Event Published Successfully**\n\n**Message:** {message}\n**Type:** {event_type}\n**Instance:** {get_instance_id()}"
            else:
                return (
                    f"⚠️ **Partial Success:** {failed_count} entries failed to publish"
                )
        else:
            return f"❌ **Publish Failed:** {result.get('error', 'Unknown error')}"

    elif action == "subscribe":
        events = subscribe_events_aws(limit)

        if not events:
            return "📭 **No recent events from other research instances**"

        result = f"📬 **Recent Distributed Events ({len(events)}):**\n\n"

        for event in events[:limit]:
            timestamp = event.get("timestamp", "unknown")
            instance = event.get("instance_id", "unknown")
            event_type = event.get("event_type", "general")
            message = event.get("message", "")

            result += f"**[{timestamp}]** `{instance}` ({event_type})\n{message}\n\n"

        return result.strip()

    else:
        return f"❌ **Error:** Unknown action '{action}'. Use: status, config, publish, or subscribe"
