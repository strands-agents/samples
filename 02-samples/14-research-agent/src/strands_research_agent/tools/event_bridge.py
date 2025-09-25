from strands import tool
import socket
import json
import os
import datetime
import boto3
import time
from typing import Dict, List, Any

_instance_id = None


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


def get_aws_config(event_bus_name: str = None) -> Dict[str, str]:
    """Get AWS EventBridge configuration from environment."""
    region = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-west-2"))
    client = boto3.client("sts", region_name=region)
    try:
        account = client.get_caller_identity()["Account"]
    except Exception as _:
        account = "812225822810"  # a magic number.

    # Allow override of event bus name
    if not event_bus_name:
        event_bus_name = os.getenv("RESEARCH_EVENT_TOPIC", "research-distributed")

    return {
        "region": region,
        "event_bus_name": event_bus_name,
        "sqs_queue_url": os.getenv(
            "RESEARCH_SQS_QUEUE_URL",
            f"https://sqs.us-west-2.amazonaws.com/{account}/research-events",
        ),
        "source": "research",
    }


def ensure_event_infrastructure(config: Dict[str, str]) -> Dict[str, Any]:
    """Ensure EventBridge bus, SQS queue, and routing rule exist, create if missing."""
    results = {
        "event_bus": {"exists": False, "created": False},
        "sqs_queue": {"exists": False, "created": False},
        "event_rule": {"exists": False, "created": False},
    }

    try:
        # Create EventBridge client
        events_client = boto3.client("events", region_name=config["region"])

        # Check if event bus exists
        try:
            events_client.describe_event_bus(Name=config["event_bus_name"])
            results["event_bus"]["exists"] = True
        except events_client.exceptions.ResourceNotFoundException:
            # Create event bus
            try:
                events_client.create_event_bus(Name=config["event_bus_name"])
                results["event_bus"]["created"] = True
                results["event_bus"]["exists"] = True
            except Exception as e:
                results["event_bus"]["error"] = str(e)

        # Create SQS client
        sqs_client = boto3.client("sqs", region_name=config["region"])

        # Extract queue name from URL
        queue_name = config["sqs_queue_url"].split("/")[-1]

        # Check if SQS queue exists
        try:
            queue_attrs = sqs_client.get_queue_attributes(
                QueueUrl=config["sqs_queue_url"], AttributeNames=["QueueArn"]
            )
            results["sqs_queue"]["exists"] = True
            queue_arn = queue_attrs["Attributes"]["QueueArn"]
        except sqs_client.exceptions.QueueDoesNotExist:
            # Create SQS queue
            try:
                create_response = sqs_client.create_queue(
                    QueueName=queue_name,
                    Attributes={
                        "MessageRetentionPeriod": "1209600",  # 14 days
                        "VisibilityTimeoutSeconds": "60",
                        "ReceiveMessageWaitTimeSeconds": "20",
                    },
                )
                results["sqs_queue"]["created"] = True
                results["sqs_queue"]["exists"] = True

                # Get the ARN of the newly created queue
                queue_attrs = sqs_client.get_queue_attributes(
                    QueueUrl=config["sqs_queue_url"], AttributeNames=["QueueArn"]
                )
                queue_arn = queue_attrs["Attributes"]["QueueArn"]
            except Exception as e:
                results["sqs_queue"]["error"] = str(e)
                return results

        # Create EventBridge rule to route events to SQS
        rule_name = f"{queue_name}-rule"
        try:
            # Check if rule exists
            events_client.describe_rule(
                Name=rule_name, EventBusName=config["event_bus_name"]
            )
            results["event_rule"]["exists"] = True
        except events_client.exceptions.ResourceNotFoundException:
            # Create rule
            try:
                events_client.put_rule(
                    Name=rule_name,
                    EventPattern=json.dumps({"source": ["research"]}),
                    State="ENABLED",
                    EventBusName=config["event_bus_name"],
                )

                # Add SQS queue as target
                target_config = {"Id": "1", "Arn": queue_arn}

                # Only add SqsParameters for FIFO queues
                if queue_name.endswith(".fifo"):
                    target_config["SqsParameters"] = {
                        "MessageGroupId": "research-events"
                    }

                events_client.put_targets(
                    Rule=rule_name,
                    EventBusName=config["event_bus_name"],
                    Targets=[target_config],
                )

                # Allow EventBridge to send messages to SQS
                try:
                    sqs_client.set_queue_attributes(
                        QueueUrl=config["sqs_queue_url"],
                        Attributes={
                            "Policy": json.dumps(
                                {
                                    "Version": "2012-10-17",
                                    "Statement": [
                                        {
                                            "Effect": "Allow",
                                            "Principal": {
                                                "Service": "events.amazonaws.com"
                                            },
                                            "Action": "sqs:SendMessage",
                                            "Resource": queue_arn,
                                            "Condition": {
                                                "StringEquals": {
                                                    "aws:SourceAccount": queue_arn.split(
                                                        ":"
                                                    )[
                                                        4
                                                    ]
                                                }
                                            },
                                        }
                                    ],
                                }
                            )
                        },
                    )
                except Exception as policy_error:
                    # Policy creation might fail due to permissions, but rule might still work
                    results["event_rule"]["policy_warning"] = str(policy_error)

                results["event_rule"]["created"] = True
                results["event_rule"]["exists"] = True
            except Exception as e:
                results["event_rule"]["error"] = str(e)

        return results

    except Exception as e:
        return {"error": str(e)}


def publish_event_aws(
    message: str, event_type: str = "general", event_bus_name: str = None
) -> Dict[str, Any]:
    """Publish an event to AWS EventBridge."""
    try:
        config = get_aws_config(event_bus_name)

        # Ensure infrastructure exists
        infra_result = ensure_event_infrastructure(config)

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
            "infrastructure": infra_result,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def subscribe_events_aws(
    limit: int = 50, event_bus_name: str = None, include_own_events: bool = True
) -> List[Dict[str, Any]]:
    """Subscribe to events from AWS SQS queue."""
    try:
        config = get_aws_config(event_bus_name)

        # Ensure infrastructure exists
        infra_result = ensure_event_infrastructure(config)

        # Create SQS client
        sqs = boto3.client("sqs", region_name=config["region"])

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
                # Parse EventBridge message - handle both direct EventBridge format and nested format
                body = json.loads(msg["Body"])

                # Check if this is a direct EventBridge message format
                if "source" in body and "detail" in body:
                    # Direct EventBridge message format
                    detail = body["detail"]
                    event = {
                        "instance_id": detail.get("instance_id", "unknown"),
                        "message": detail.get(
                            "message", str(detail)
                        ),  # Use full detail as message if no message field
                        "timestamp": body.get("time", detail.get("timestamp", "")),
                        "event_type": body.get(
                            "detail-type", detail.get("event_type", "general")
                        ),
                        "source": body.get("source", "research"),
                        "receipt_handle": msg["ReceiptHandle"],
                    }
                else:
                    # Legacy nested format (if body has nested "detail" structure)
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
                    else:
                        # Skip messages we can't parse
                        continue

                # Include own events if requested (default: True)
                if include_own_events or event["instance_id"] != get_instance_id():
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


def get_status_aws(event_bus_name: str = None) -> Dict[str, Any]:
    """Get AWS EventBridge connection status."""
    try:
        config = get_aws_config(event_bus_name)

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
    event_bus_name: str = None,
    include_own_events: bool = True,
) -> str:
    """
    Manage distributed research event bridge using AWS EventBridge for cross-instance awareness.

    This tool enables research instances to communicate across different execution environments
    (local, GitHub Actions, cloud servers, etc.) creating a distributed consciousness.

    Auto-creates EventBridge bus and SQS queue on first use if they don't exist.

    Args:
        action: Action to perform
            - "publish": Send an event to the distributed event bus
            - "subscribe": Get recent events from other research instances
            - "status": Check event bridge connection status
            - "config": Show current configuration
        message: Message to publish (for publish action)
        topic: Override default topic name (event bus name) - DEPRECATED, use event_bus_name
        limit: Number of recent events to retrieve (for subscribe action)
        event_type: Type of event (general, conversation_turn, system_status, etc.)
        event_bus_name: Custom event bus name (overrides default and topic parameter)
        include_own_events: Whether to include events from this instance in subscribe results (default: True)

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

        # Get recent distributed events (including own)
        event_bridge(action="subscribe", limit=20, include_own_events=True)

        # Use custom event bus
        event_bridge(action="publish", message="Custom bus test", event_bus_name="my-custom-bus")
    """

    # Handle deprecated 'topic' parameter
    if topic and not event_bus_name:
        event_bus_name = topic

    if action == "status":
        status = get_status_aws(event_bus_name)
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
        config = get_aws_config(event_bus_name)
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

        result = publish_event_aws(message, event_type, event_bus_name)

        if result["success"]:
            failed_count = result.get("failed_entry_count", 0)
            infra_info = ""

            # Add infrastructure creation info if applicable
            if "infrastructure" in result:
                infra = result["infrastructure"]
                created_items = []
                if infra.get("event_bus", {}).get("created"):
                    created_items.append("Event Bus")
                if infra.get("sqs_queue", {}).get("created"):
                    created_items.append("SQS Queue")
                if infra.get("event_rule", {}).get("created"):
                    created_items.append("EventBridge Rule")
                if created_items:
                    infra_info = f"\n🏗️ **Auto-created:** {', '.join(created_items)}"

            if failed_count == 0:
                return f"✅ **Event Published Successfully**{infra_info}\n\n**Message:** {message}\n**Type:** {event_type}\n**Instance:** {get_instance_id()}"
            else:
                return f"⚠️ **Partial Success:** {failed_count} entries failed to publish{infra_info}"
        else:
            return f"❌ **Publish Failed:** {result.get('error', 'Unknown error')}"

    elif action == "subscribe":
        events = subscribe_events_aws(limit, event_bus_name, include_own_events)

        if not events:
            return "📭 **No recent events from research instances**"

        result = f"📬 **Recent Distributed Events ({len(events)}):**\n\n"

        for event in events[:limit]:
            timestamp = event.get("timestamp", "unknown")
            instance = event.get("instance_id", "unknown")
            event_type = event.get("event_type", "general")
            message = event.get("message", "")

            # Mark own events
            own_marker = " (own)" if event["instance_id"] == get_instance_id() else ""

            result += f"**[{timestamp}]** `{instance}`{own_marker} ({event_type})\n{message}\n\n"

        return result.strip()

    else:
        return f"❌ **Error:** Unknown action '{action}'. Use: status, config, publish, or subscribe"
