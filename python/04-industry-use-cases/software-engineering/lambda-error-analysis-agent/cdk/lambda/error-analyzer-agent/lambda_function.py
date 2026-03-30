#!/usr/bin/env python3
"""
Error Analyzer Agent Lambda with Strands Agent integration
Processes task events and provides intelligent error analysis using AI
"""

import json
import os
from agent import analyze_error  # Import Strands Agent

# Generic event types
TASK_FAILED_DETAIL_TYPE = "TaskFailed"
TASK_SUCCEEDED_DETAIL_TYPE = "TaskSucceeded"
TASK_UPDATE_DETAIL_TYPE = "TaskUpdate"

def lambda_handler(event, context):
    """Lambda handler for processing task events with AI-powered error analysis"""
    
    # Generate CloudWatch link from event data
    cloud_watch_link = ""
    if "detail" in event and "lambda" in event["detail"]:
        region = os.environ.get('AWS_REGION', 'us-east-1')
        log_group = event["detail"]["lambda"]["logGroupName"]
        log_stream = event["detail"]["lambda"]["logStreamName"]
        cloud_watch_link = f"https://console.aws.amazon.com/cloudwatch/home?region={region}#logEventViewer:group={log_group};stream={log_stream}"

    detail_type = event["detail-type"]
    
    # Handle both success and failure events
    if detail_type == TASK_FAILED_DETAIL_TYPE:
        return handle_task_failed(event, cloud_watch_link)
    elif detail_type in [TASK_SUCCEEDED_DETAIL_TYPE, TASK_UPDATE_DETAIL_TYPE]:
        return handle_task_succeeded(event, cloud_watch_link)
    else:
        return {"statusCode": 200, "body": "Event type not handled"}

def handle_task_failed(event, cloud_watch_link):
    """Handle failed tasks with AI-enhanced error analysis"""
    
    detail = event["detail"]
    
    # Extract error information
    error_message = detail.get("error", {}).get("message", "Unknown error")
    
    # Extract lambda information
    lambda_info = detail.get("lambda", {})
    function_name = lambda_info.get("functionName", "Unknown")
    request_id = lambda_info.get("requestId", "Unknown")
    
    print(f"🔍 Processing Failed Task:")
    print(f"   • Function: {function_name}")
    print(f"   • Request ID: {request_id}")
    print(f"   • Error: {error_message}")
    print(f"   • CloudWatch: {cloud_watch_link}")
    
    # Call Strands Agent for intelligent error analysis
    try:
        print(f"🤖 Calling Strands Agent for error analysis...")
        enhanced_analysis = analyze_error(event)
        
        print(f"📊 Agent Analysis Result:")
        print(json.dumps(enhanced_analysis, indent=2))
        
        if enhanced_analysis and "error" in enhanced_analysis and "agent_analysis" in enhanced_analysis:
            ai_analysis = enhanced_analysis["agent_analysis"]
            
            # Check if agent analysis succeeded
            if ("AGENT ANALYSIS FAILED" not in ai_analysis and 
                "AI Analysis temporarily unavailable" not in ai_analysis):
                # Combine original error with AI analysis
                original_error = enhanced_analysis["error"]
                enhanced_message = f"{original_error}\n\n--- AI Analysis ---\n{ai_analysis}"
                print(f"✨ Enhanced error message with AI analysis")
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "status": "analyzed",
                        "error": original_error,
                        "analysis": ai_analysis,
                        "cloudwatch_link": cloud_watch_link
                    })
                }
    except Exception as e:
        print(f"⚠️ Error during AI analysis: {e}")
    
    # Return original error if AI analysis fails
    return {
        "statusCode": 200,
        "body": json.dumps({
            "status": "failed",
            "error": error_message,
            "cloudwatch_link": cloud_watch_link
        })
    }

def handle_task_succeeded(event, cloud_watch_link):
    """Handle successful tasks"""
    
    detail = event["detail"]
    
    # Extract lambda information
    lambda_info = detail.get("lambda", {})
    function_name = lambda_info.get("functionName", "Unknown")
    request_id = lambda_info.get("requestId", "Unknown")
    
    # Get additional info if available
    additional_info = detail.get("info", "Task completed successfully")
    
    print(f"🎉 Processing Successful Task:")
    print(f"   • Function: {function_name}")
    print(f"   • Request ID: {request_id}")
    print(f"   • Info: {additional_info}")
    print(f"   • CloudWatch: {cloud_watch_link}")
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "status": "succeeded",
            "info": additional_info,
            "cloudwatch_link": cloud_watch_link
        })
    }

def process_task_event(task_event):
    """Process a task event directly (for testing)"""
    
    if not task_event:
        return {"error": "No event provided"}
    
    # Convert the EventBridge event format to the expected lambda handler format
    event_data = {
        "detail-type": task_event["DetailType"],
        "detail": json.loads(task_event["Detail"]) if isinstance(task_event["Detail"], str) else task_event["Detail"]
    }
    
    print(f"🔄 Processing {task_event['DetailType']} event...")
    
    # Call the lambda handler with the converted event
    result = lambda_handler(event_data, None)
    
    return result