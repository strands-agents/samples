import boto3
import json
from boto3.dynamodb.conditions import Key
from typing import List, Dict, Any
from datetime import datetime
import os
from .ssm_utils import load_config

# Load configuration from SSM
try:
    config = load_config()
except Exception as e:
    print(f"❌ Error loading config in dynamodb_utils: {e}")
    config = {}

# Default AWS region fallback
DEFAULT_AWS_REGION = "us-east-1"


def save_raw_query_result(user_message_uuid, user_message, sql_query, sql_query_description, result, message, table_name=None, region=None):
    """
    Store SQL query execution results and metadata in DynamoDB.
    
    Saves comprehensive query execution details including the original user question,
    SQL query, description, results, and timestamp for audit and analysis purposes.
    
    Args:
        user_message_uuid: Unique identifier for the user message
        user_message: Original user question that triggered the query
        sql_query: Executed SQL query string
        sql_query_description: Human-readable description of the query purpose
        result: Query execution results (JSON serialized)
        message: Additional context or result summary
        table_name: DynamoDB table name (optional, falls back to environment variable)
        region: AWS region (optional, falls back to environment variable)
        
    Returns:
        dict: Success status with DynamoDB response or error details
    """
    try:
        # Use provided parameters or fall back to SSM config
        aws_region = region or config.get("AWS_REGION", DEFAULT_AWS_REGION)
        raw_query_results_table = table_name or config.get("RAW_QUERY_RESULTS_TABLE_NAME")
        
        if not raw_query_results_table:
            return {"success": False, "error": "RAW_QUERY_RESULTS_TABLE_NAME not configured"}
        
        dynamodb_client = boto3.client('dynamodb', region_name=aws_region)
        
        response = dynamodb_client.put_item(
            TableName=raw_query_results_table,
            Item={
                "id": {"S": user_message_uuid},
                "my_timestamp": {"N": str(int(datetime.now().timestamp()))},
                "datetime": {"S": str(datetime.now())},
                "user_message": {"S": user_message},
                "sql_query": {"S": sql_query},
                "sql_query_description": {"S": sql_query_description},
                "data": {"S": json.dumps(result)},
                "message_result": {"S": message}
            }
        )
        
        print(f"\n💾 DYNAMODB SAVE SUCCESS")
        print("-"*40)
        print(f"🆔 ID: {user_message_uuid}")
        print(f"📊 Table: {raw_query_results_table}")
        print("-"*40)
        return {"success": True, "response": response}
        
    except Exception as e:
        print(f"\n❌ DYNAMODB SAVE ERROR")
        print("-"*40)
        print(f"🚨 Error: {str(e)}")
        print(f"📊 Table: {raw_query_results_table}")
        print("-"*40)
        return {"success": False, "error": str(e)}


def read_messages_by_session(session_id: str, last_number_of_messages: int = 20, table_name: str = None, region: str = None) -> List[Dict[str, Any]]:
    """
    Retrieve conversation history from DynamoDB with pagination and JSON parsing.
    
    Queries messages by session ID, parses JSON message content, and returns
    in chronological order for conversation context. Handles missing table gracefully.
    
    Args:
        session_id: Session identifier to query
        last_number_of_messages: Maximum messages to retrieve (default: 20)
        table_name: DynamoDB table name (optional, falls back to environment variable)
        region: AWS region (optional, falls back to environment variable)
        
    Returns:
        List[Dict]: Parsed message objects in chronological order, empty if table not configured
    """
    # Use provided parameters or fall back to SSM config
    aws_region = region or config.get("AWS_REGION", DEFAULT_AWS_REGION)
    conversation_table = table_name or config.get("CONVERSATION_TABLE_NAME")
    
    if not conversation_table:
        print(f"\n⚠️ CONFIGURATION WARNING")
        print("-"*40)
        print(f"📋 Message: CONVERSATION_TABLE_NAME not set")
        print(f"📤 Action: Returning empty message history")
        print("-"*40)
        return []
    
    try:
        dynamodb_resource = boto3.resource('dynamodb', region_name=aws_region)
        table = dynamodb_resource.Table(conversation_table)
        
        response = table.query(
            KeyConditionExpression=Key('session_id').eq(session_id),
            ProjectionExpression='message',
            Limit=last_number_of_messages,
            ScanIndexForward=False  # Sort by message_id DESC (most recent first)
        )
        
        messages = []
        for item in response.get('Items', []):
            message_data = item.get('message')
            if message_data:
                try:
                    messages.append(json.loads(message_data))
                except json.JSONDecodeError as e:
                    print(f"\n🔧 JSON PARSE ERROR")
                    print("-"*40)
                    print(f"🚨 Error: {e}")
                    print(f"📄 Context: Message JSON parsing")
                    print("-"*40)
                    continue
        
        # Reverse to get chronological order (oldest first)
        messages.reverse()
        
        return messages
        
    except Exception as e:
        print(f"\n❌ DYNAMODB READ ERROR")
        print("-"*40)
        print(f"🚨 Error: {e}")
        print(f"📊 Table: {conversation_table}")
        print(f"🔗 Session: {session_id}")
        print("-"*40)
        return []


def messages_objects_to_strings(obj_array):
    """
    Filter and convert message objects focusing on user/assistant text and SQL tool usage.
    
    Extracts meaningful conversation content by filtering for:
    - Text-only user/assistant messages
    - SQL query executions with descriptions
    - Table information tool results
    
    Args:
        obj_array (List): Array of message objects from conversation history
        
    Returns:
        List[str]: Filtered message objects as JSON strings for storage
    """
    filtered_objs = []
    
    for i, obj in enumerate(obj_array):
        # Simple text messages from user or assistant
        if obj["role"] in ["user", "assistant"] and "content" in obj:
            # Check if content contains only text items (no toolUse or toolResult)
            has_only_text = True
            for item in obj["content"]:
                if "text" not in item:
                    has_only_text = False
                    break            
            if has_only_text:
                filtered_objs.append(obj)
        
        # Messages where assistant is using a tool
        if obj["role"] == "assistant" and "content" in obj:
            for item in obj["content"]:
                if "toolUse" in item and "name" in item['toolUse'] and item['toolUse']['name']=="execute_sql_query":
                    #data = { 'toolUsed': 'execute_sql_query', 'input': item['toolUse']['input'] }
                    data = f"{item['toolUse']['input']['description']}: {item['toolUse']['input']['sql_query']}"
                    filtered_objs.append({ 'role': 'assistant', 'content': [{ 'text' : data }] })
                    break

        if obj["role"] == "user" and "content" in obj:
            for item in obj["content"]:
                if "toolResult" in item and "content" in item['toolResult'] and len(item['toolResult']['content'])>0:
                    for content_item in item['toolResult']['content']:
                        if "text" in content_item:
                            if "'toolUsed': 'get_tables_information'" in content_item["text"]:
                                filtered_objs.append({ 'role': 'user', 'content': [{ 'text' : content_item["text"]}] })
                                break

    return [json.dumps(obj) for obj in filtered_objs]


def save_messages(session_id: str, message_uuid: str, starting_message_id: int, messages: List[str]) -> bool:
    """
    Batch write filtered conversation messages to DynamoDB starting from specific ID.
    
    Filters messages through messages_objects_to_strings() to extract meaningful content,
    then batch writes to conversation table with incremental message IDs.
    
    Args:
        session_id (str): Session UUID for conversation grouping
        message_uuid (str): Message UUID for tracking
        starting_message_id (int): Starting message ID for incremental numbering
        messages (List[str]): Raw message objects to filter and save
        
    Returns:
        bool: True if batch write successful, False on error
    """
    
    messages_to_save = messages_objects_to_strings(messages)

    print(f"\n📝 MESSAGE PROCESSING COMPLETE")
    print("-"*40)
    print(f"📊 Final Messages Count: {len(messages_to_save)}")
    print(f"🔗 Session ID: {session_id}")
    print("-"*40)

    # Use SSM config for table name and region
    conversation_table = config.get("CONVERSATION_TABLE_NAME")
    aws_region = config.get("AWS_REGION", DEFAULT_AWS_REGION)
    
    if not conversation_table:
        print(f"\n⚠️ CONFIGURATION WARNING")
        print("-"*40)
        print(f"📋 Message: CONVERSATION_TABLE_NAME not set")
        print(f"📤 Action: Skipping message save")
        print("-"*40)
        return False
    dynamodb = boto3.resource('dynamodb', region_name=aws_region)
    table = dynamodb.Table(conversation_table)
    
    try:
        with table.batch_writer() as batch:
            for i, message_text in enumerate(messages_to_save):
                if i < starting_message_id:
                    continue
                message_id = starting_message_id
                batch.put_item(
                    Item={
                        'session_id': session_id,
                        'message_id': message_id,
                        'message_uuid': message_uuid,
                        'message': message_text
                    }
                )
                starting_message_id += 1
        return True
    except Exception as e:
        print(f"\n❌ MESSAGE WRITE ERROR")
        print("-"*40)
        print(f"🚨 Error: {e}")
        print(f"📊 Table: {conversation_table}")
        print(f"🔗 Session: {session_id}")
        print("-"*40)
        return False