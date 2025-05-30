import boto3
import json
from boto3.dynamodb.conditions import Key
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import pprint

# Environment variables configuration
ENV = {
    "RAW_QUERY_RESULTS_TABLE_NAME": os.environ.get("RAW_QUERY_RESULTS_TABLE_NAME"),
    "CONVERSATION_TABLE_NAME": os.environ.get("CONVERSATION_TABLE_NAME"),
    "AWS_REGION": os.environ.get("AWS_REGION", "us-east-1")
}

def save_raw_query_result(user_prompt_uuid, user_prompt, sql_query, sql_query_description, result, message):
    """
    Save query execution results to DynamoDB
    
    Args:
        user_prompt_uuid: Unique identifier for the user prompt
        user_prompt: The original user question
        sql_query: The executed SQL query
        sql_query_description: A description of the SQL query that was executed
        result: The query results
        message_result: Additional information of the result
        
    Returns:
        dict: Response from DynamoDB put_item operation or error details
    """
    try:
        dynamodb_client = boto3.client('dynamodb', region_name=ENV["AWS_REGION"])
        
        response = dynamodb_client.put_item(
            TableName=ENV["RAW_QUERY_RESULTS_TABLE_NAME"],
            Item={
                "id": {"S": user_prompt_uuid},
                "my_timestamp": {"N": str(int(datetime.now().timestamp()))},
                "datetime": {"S": str(datetime.now())},
                "user_prompt": {"S": user_prompt},
                "sql_query": {"S": sql_query},
                "sql_query_description": {"S": sql_query_description},
                "data": {"S": json.dumps(result)},
                "message_result": {"S": message}
            },
        )
        
        print(f"Data saved to DynamoDB with ID: {user_prompt_uuid}")
        return {"success": True, "response": response}
        
    except Exception as e:
        print(f"Error saving to DynamoDB: {str(e)}")
        return {"success": False, "error": str(e)}


def read_messages_by_session(
    session_id: str
) -> List[Dict[str, Any]]:
    """
    Read messages from a table by session_id with pagination.
    
    Args:
        session_id: The session ID to query for
        
    Returns:
        List of message objects containing only message attribute
    """
    
    dynamodb_resource = boto3.resource('dynamodb', region_name=ENV["AWS_REGION"])
    table = dynamodb_resource.Table(ENV["CONVERSATION_TABLE_NAME"])
    
    messages = []
    last_evaluated_key = None
    
    while True:
        query_params = {
            'KeyConditionExpression': Key('session_id').eq(session_id),
            'ProjectionExpression': 'message',
            'Limit': 100
        }
        
        # Add pagination token if this isn't the first page
        if last_evaluated_key:
            query_params['ExclusiveStartKey'] = last_evaluated_key
        
        response = table.query(**query_params)
        
        # Add the items to our result list
        for item in response.get('Items', []):
            messages.append(json.loads(item.get('message')))
        
        # Update the pagination token
        last_evaluated_key = response.get('LastEvaluatedKey')
        
        # If there's no pagination token, we've reached the end
        if not last_evaluated_key:
            break
    
    return messages


def messages_objects_to_strings(obj_array):
    """
    Convert message objects to a filtered list focusing on user/assistant interactions.
    
    Filters and converts message objects to include only text content and specific
    tool interactions like SQL query execution.
    
    Args:
        obj_array (List): Array of message objects to process
        
    Returns:
        List[str]: List of filtered message objects converted to JSON strings
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
                    data = f"{item['toolUse']['input']["description"]}: {item['toolUse']['input']["sql_query"]}"
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


def save_messages(session_id: str, prompt_uuid: str, starting_message_id: int, 
                         messages: List[str]) -> bool:
    """
    Write multiple messages to a session starting from a specific message_id.
    
    Args:
        session_id (str): The UUID of the session
        prompt_uuid (str): The UUID of the prompt
        starting_message_id (int): The message_id to start with
        messages (List[str]): List of message objects to write
        
    Returns:
        bool: True if successful, False otherwise
    """
    
    messages_to_save = messages_objects_to_strings(messages)

    print("Final messages length: " + str(len(messages_to_save)))

    dynamodb = boto3.resource('dynamodb', region_name=ENV["AWS_REGION"])
    table = dynamodb.Table(ENV["CONVERSATION_TABLE_NAME"])
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
                        'prompt_uuid': prompt_uuid,
                        'message': message_text
                    }
                )
                starting_message_id += 1
        return True
    except Exception as e:
        print(f"Error writing messages: {e}")
        return False