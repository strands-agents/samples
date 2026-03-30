#!/usr/bin/env python3
"""
Strands Agent for intelligent automation error analysis
Provides context-aware error analysis using multiple data sources
"""

import json
import os
import uuid
import boto3
import zipfile
import io
import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import retrieve

# Initialize AWS clients
cloudwatch_logs = boto3.client('logs')
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')

# Configure Knowledge Base for retrieve tool
KNOWLEDGE_BASE_ID = os.environ.get('KNOWLEDGE_BASE_ID')
if KNOWLEDGE_BASE_ID:
    print(f"Knowledge Base configured: {KNOWLEDGE_BASE_ID}")
else:
    print("Warning: KNOWLEDGE_BASE_ID not found in environment variables")

# Configuration switches for DynamoDB storage (to prevent large items)
STORE_CLOUDWATCH_LOGS = os.environ.get('STORE_CLOUDWATCH_LOGS', 'true').lower() == 'true'
STORE_SOURCE_CODE = os.environ.get('STORE_SOURCE_CODE', 'true').lower() == 'true'

# Log retrieval limits
MAX_CLOUDWATCH_LOG_EVENTS = 10000  # CloudWatch API limit per request

# Model selection switch (default: Claude Sonnet 4)
USE_SONNET_4 = os.environ.get('USE_SONNET_4', 'true').lower() == 'true'

# Source code size limits for both S3 and Lambda retrieval
MAX_FILE_SIZE = 25000    # 25KB per file (up from 20KB)
MAX_TOTAL_SIZE = 100000  # 100KB total (up from 50KB)

print(f"Storage configuration - CloudWatch logs: {STORE_CLOUDWATCH_LOGS}, Source code: {STORE_SOURCE_CODE}")
print(f"Model configuration - Using Sonnet 4: {USE_SONNET_4}")
print(f"Source code limits - Max file: {MAX_FILE_SIZE//1000}KB, Max total: {MAX_TOTAL_SIZE//1000}KB")

# Global variable to capture tool execution results
tool_execution_results = {}

@tool
def fetch_cloudwatch_logs(log_group: str, log_stream: str, request_id: str = None) -> str:
    """Fetch CloudWatch logs filtered by request ID and error patterns"""
    global tool_execution_results
    try:
        # Parse CloudWatch link to extract log group and stream if needed
        original_log_group = log_group
        if "logEventViewer" in log_group and "group=" in log_group:
            try:
                # Extract from CloudWatch console URL
                parts = log_group.split("group=")[1].split(";stream=")
                log_group = parts[0]
                if len(parts) > 1 and not log_stream:
                    log_stream = parts[1]
                print(f"Parsed CloudWatch URL: {original_log_group} -> {log_group}/{log_stream}")
            except Exception as e:
                print(f"Failed to parse CloudWatch URL, using as-is: {e}")
                # Use original values if parsing fails
        
        print(f"Fetching logs from {log_group}/{log_stream}" + (f" for request {request_id}" if request_id else ""))
        
        # Paginate through CloudWatch logs to find the specific Request ID
        all_events = []
        next_token = None
        pages_fetched = 0
        max_pages = 10  # Safety limit: 10 pages * 10K events = 100K events max
        
        while pages_fetched < max_pages:
            # Build API parameters
            params = {
                'logGroupName': log_group,
                'logStreamName': log_stream,
                'limit': MAX_CLOUDWATCH_LOG_EVENTS,
                'startFromHead': False  # Start from newest logs
            }
            if next_token:
                params['nextToken'] = next_token
            
            # Fetch page
            response = cloudwatch_logs.get_log_events(**params)
            events = response.get('events', [])
            pages_fetched += 1
            
            # Get pagination tokens
            next_forward_token = response.get('nextForwardToken')
            next_backward_token = response.get('nextBackwardToken')
            
            # Add events to collection
            all_events.extend(events)
            
            # Check if we've reached the end
            if next_forward_token == next_backward_token:
                break
            
            # If no events but tokens differ, we're in a gap - continue paginating
            if not events and next_forward_token != next_backward_token:
                next_token = next_backward_token
                continue
            
            # If no events and no valid continuation, stop
            if not events:
                break
            
            # Check if we found the START of the execution (ensures complete logs)
            if request_id:
                # More efficient check - avoid string conversion
                for event in events:
                    if f"START RequestId: {request_id}" in event['message']:
                        print(f"Found execution in {pages_fetched} page(s), retrieved {len(all_events)} events")
                        break
                else:
                    # START not found, continue to next page
                    next_token = next_backward_token
                    continue
                # START found, exit loop
                break
            
            # Use backward token to go further back in time
            next_token = next_backward_token
        
        # Filter by request ID using execution boundaries (most accurate)
        if request_id:
            execution_events = extract_execution_logs(all_events, request_id)
            if execution_events:
                print(f"Found {len(execution_events)} logs for execution {request_id}")
                logs_result = format_log_events(execution_events, log_group, log_stream)
                # Store the result globally for later capture
                tool_execution_results['cloudwatch_logs'] = logs_result
                return logs_result
            else:
                print(f"No execution logs found for request {request_id} in log stream")
                error_result = f"No logs found for request ID {request_id} in {log_group}/{log_stream}. The execution may be in a different log stream or the request ID may be incorrect."
                tool_execution_results['cloudwatch_logs'] = error_result
                return error_result
        else:
            print(f"No request ID provided, cannot retrieve specific execution logs")
            error_result = f"No request ID provided for log retrieval from {log_group}/{log_stream}. Cannot retrieve specific execution logs without request ID."
            tool_execution_results['cloudwatch_logs'] = error_result
            return error_result
        
    except Exception as e:
        error_msg = f"Error fetching CloudWatch logs: {str(e)}"
        print(f"ERROR: {error_msg}")
        tool_execution_results['cloudwatch_logs'] = error_msg
        return error_msg

def extract_execution_logs(all_events: list, request_id: str) -> list:
    """Extract all logs between START and REPORT for a specific Lambda execution"""
    try:
        execution_events = []
        start_found = False
        
        for event in all_events:
            message = event['message']
            
            # Look for START marker
            if f"START RequestId: {request_id}" in message:
                start_found = True
                execution_events.append(event)
                continue
            
            # If we found START, collect all logs until REPORT
            if start_found:
                execution_events.append(event)
                
                # Stop at REPORT marker (end of execution)
                if f"REPORT RequestId: {request_id}" in message:
                    break
        
        print(f"Execution boundary detection: START found={start_found}, collected {len(execution_events)} events")
        return execution_events
        
    except Exception as e:
        print(f"Error in execution boundary detection: {e}")
        # Fallback to simple request ID filtering
        return [e for e in all_events if request_id in e['message']]

def format_log_events(events: list, log_group: str, log_stream: str) -> str:
    """Format log events for agent analysis"""
    if not events:
        return f"No log events found in {log_group}/{log_stream}"
    
    log_entries = []
    for event in events:
        timestamp = datetime.fromtimestamp(event['timestamp'] / 1000, tz=timezone.utc)
        log_entries.append(f"[{timestamp.isoformat()}] {event['message']}")
    
    logs_text = "\n".join(log_entries)
    return f"CloudWatch Logs for {log_group}/{log_stream}:\n{logs_text}"

def store_analysis_result(analysis: Dict[str, Any]) -> str:
    """Store full analysis result in DynamoDB for review and improvement"""
    try:
        table_name = os.environ.get('DYNAMODB_TABLE_NAME')
        if not table_name:
            return "DynamoDB table name not configured"
        
        table = dynamodb.Table(table_name)
        
        # Create analysis record with proper DynamoDB format
        from decimal import Decimal
        
        analysis_record = {
            # Primary keys
            'error_id': f"analysis-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8]}",
            'analysis_id': f"analysis-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8]}",
            'timestamp': analysis.get('analysis_timestamp', datetime.now(timezone.utc).isoformat()),
            
            # Original event and response
            'original_event': json.dumps(analysis.get('original_event', {})),  # Changed from 'error_event'
            'agent_analysis': str(analysis.get('agent_analysis', '')),  # Now matches source
            
            # Tool execution results (actual data captured from tools)
            'tools_used': analysis.get('tools_used', []),
            'source_code': str(analysis.get('source_code', '')) if STORE_SOURCE_CODE else '[Source code storage disabled]',
            'cloudwatch_logs': str(analysis.get('cloudwatch_logs', '')) if STORE_CLOUDWATCH_LOGS else '[CloudWatch logs storage disabled]',
            'knowledge_base_context': str(analysis.get('knowledge_base_context', '')),
            
            # Extracted recommendations
            'recommendations': analysis.get('recommendations', []),
            
            # Event metadata
            'error_message': str(analysis.get('error_message', '')),
            'function_name': str(analysis.get('function_name', '')),
            'request_id': str(analysis.get('request_id', '')),
            'stack_trace': str(analysis.get('stack_trace', '')),
            'log_group': str(analysis.get('log_group', '')),
            'log_stream': str(analysis.get('log_stream', '')),
            
            # Confidence and evidence quality
            'confidence_score': Decimal(str(analysis.get('confidence_score', 0.0))),
            'confidence_level': str(analysis.get('confidence_level', 'unknown')),
            'confidence_factors': analysis.get('confidence_factors', []),
            'evidence_quality': json.dumps(analysis.get('evidence_quality', {})),
            
            # Analysis timing information
            'analysis_duration_seconds': Decimal(str(analysis.get('analysis_duration_seconds', 0.0))),
            'analysis_duration_mm_ss': str(analysis.get('analysis_duration_mm_ss', '00:00')),
            
            # Analysis metadata
            'analysis_version': '3.2'  # Track schema version
        }
        
        # Store in DynamoDB
        table.put_item(Item=analysis_record)
        
        print(f"Stored analysis result: {analysis_record['analysis_id']}")
        return f"Analysis stored successfully: {analysis_record['analysis_id']}"
        
    except Exception as e:
        error_msg = f"Error storing analysis: {str(e)}"
        print(f"ERROR: {error_msg}")
        return error_msg

@tool
def fetch_source_code(lambda_name: str) -> str:
    """Fetch Lambda source code from S3 with Lambda function fallback"""
    global tool_execution_results
    
    try:
        # First, try S3 source bucket (existing logic)
        s3_result = try_s3_source_code(lambda_name)
        if s3_result['success']:
            tool_execution_results['source_code'] = s3_result['content']
            tool_execution_results['source_code_method'] = 'S3 source bucket'
            return s3_result['content']
        
        print(f"S3 source failed: {s3_result['error']}. Trying Lambda function fallback...")
        
        # Fallback: Try Lambda GetFunction API
        lambda_result = try_lambda_function_code(lambda_name)
        if lambda_result['success']:
            tool_execution_results['source_code'] = lambda_result['content']
            tool_execution_results['source_code_method'] = 'Lambda function ZIP'
            return lambda_result['content']
        
        # Both methods failed
        error_msg = f"All source code retrieval methods failed. S3: {s3_result['error']}. Lambda: {lambda_result['error']}"
        tool_execution_results['source_code'] = error_msg
        tool_execution_results['source_code_method'] = 'Failed'
        return error_msg
        
    except Exception as e:
        error_msg = f"Error in source code retrieval: {str(e)}"
        print(f"ERROR: {error_msg}")
        tool_execution_results['source_code'] = error_msg
        tool_execution_results['source_code_method'] = 'Exception'
        return error_msg

def try_s3_source_code(lambda_name: str) -> dict:
    """Try to fetch source code from S3 bucket"""
    try:
        bucket_name = os.environ.get('SOURCE_CODE_BUCKET')
        if not bucket_name:
            return {'success': False, 'error': 'Source code bucket not configured'}
        
        if not lambda_name:
            return {'success': False, 'error': 'No Lambda function name provided'}
        
        # Direct mapping: lambdas/{function_name}/
        folder = f"lambdas/{lambda_name}/"
        print(f"Fetching source code from S3: {folder}")
        
        # Get all Python files in the folder
        source_files = {}
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(
            Bucket=bucket_name,
            Prefix=folder
        )
        
        total_size = 0
        
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    if obj['Key'].endswith('.py'):
                        # Check file size before downloading
                        file_size = obj['Size']
                        if file_size > MAX_FILE_SIZE:
                            print(f"Skipping large file {obj['Key']}: {file_size} bytes")
                            continue
                        
                        if total_size + file_size > MAX_TOTAL_SIZE:
                            print(f"Reached size limit, skipping remaining files")
                            break
                        
                        response = s3.get_object(
                            Bucket=bucket_name,
                            Key=obj['Key']
                        )
                        content = response['Body'].read().decode('utf-8')
                        file_name = obj['Key'].split('/')[-1]
                        source_files[file_name] = content
                        total_size += len(content)
                        print(f"Retrieved source code: {file_name} ({len(content)} chars)")
        
        if not source_files:
            return {'success': False, 'error': f'No Python files found in {folder}'}
        
        # Format the response
        formatted_code = f"Source code for {lambda_name} ({total_size} chars total, from S3 source bucket):\n"
        for file_name, content in source_files.items():
            formatted_code += f"\n=== {file_name} ===\n{content}\n"
        
        print(f"Retrieved {len(source_files)} source files from S3, {total_size} total chars")
        return {'success': True, 'content': formatted_code}
        
    except Exception as e:
        return {'success': False, 'error': f'S3 retrieval error: {str(e)}'}

def try_lambda_function_code(lambda_name: str) -> dict:
    """Try to fetch source code directly from Lambda function"""
    try:
        print(f"Fetching source code from Lambda function: {lambda_name}")
        
        # Get Lambda function details
        response = lambda_client.get_function(FunctionName=lambda_name)
        
        # Get the presigned URL for the deployment package
        code_location = response['Code']['Location']
        print(f"Downloading Lambda deployment package from: {code_location[:100]}...")
        
        # Download the ZIP file
        zip_response = requests.get(code_location, timeout=30)
        zip_response.raise_for_status()
        
        # Load ZIP file in memory
        zip_data = io.BytesIO(zip_response.content)
        
        # Extract Python files from ZIP
        source_files = {}
        total_size = 0
        
        with zipfile.ZipFile(zip_data, 'r') as zip_file:
            for file_info in zip_file.infolist():
                if file_info.filename.endswith('.py') and not file_info.is_dir():
                    # Skip obvious third-party libraries
                    if any(skip in file_info.filename.lower() for skip in 
                          ['site-packages/', '__pycache__/', '.git/', 'venv/', 'env/']):
                        continue
                    
                    # Check file size
                    if file_info.file_size > MAX_FILE_SIZE:
                        print(f"Skipping large file {file_info.filename}: {file_info.file_size} bytes")
                        continue
                    
                    if total_size + file_info.file_size > MAX_TOTAL_SIZE:
                        print(f"Reached size limit, skipping remaining files")
                        break
                    
                    # Extract and decode file content
                    try:
                        content = zip_file.read(file_info.filename).decode('utf-8')
                        file_name = file_info.filename.split('/')[-1]  # Get just filename
                        source_files[file_name] = content
                        total_size += len(content)
                        print(f"Extracted source code: {file_name} ({len(content)} chars)")
                    except UnicodeDecodeError:
                        print(f"Skipping binary file: {file_info.filename}")
                        continue
        
        if not source_files:
            return {'success': False, 'error': 'No Python source files found in Lambda deployment package'}
        
        # Format the response
        formatted_code = f"Source code for {lambda_name} ({total_size} chars total, from Lambda deployment package):\n"
        for file_name, content in source_files.items():
            formatted_code += f"\n=== {file_name} ===\n{content}\n"
        
        print(f"Retrieved {len(source_files)} source files from Lambda ZIP, {total_size} total chars")
        return {'success': True, 'content': formatted_code}
        
    except Exception as e:
        return {'success': False, 'error': f'Lambda function retrieval error: {str(e)}'}
        return {'success': False, 'error': f'Lambda function retrieval error: {str(e)}'}

@tool
def search_knowledge_base(query: str) -> str:
    """Search Knowledge Base for documentation, best practices, and error patterns"""
    global tool_execution_results
    
    try:
        print(f"Searching Knowledge Base for general knowledge: {query}")
        
        all_results = []
        retrieval_metadata = {
            'total_results': 0,
            'high_confidence_results': 0,
            'avg_score': 0.0,
            'max_score': 0.0,
            'confidence_level': 'low'
        }
        
        # Search with error-focused query
        try:
            result = retrieve.retrieve({
                "toolUseId": str(uuid.uuid4()),
                "input": {
                    "text": query,
                    "score": 0.4,
                    "numberOfResults": 5,
                    "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                    "region": os.environ.get('AWS_REGION', 'us-east-1'),
                },
            })
            
            if isinstance(result, dict) and result.get("status") == "success" and "content" in result:
                content = result["content"]
                scores = []
                
                if isinstance(content, list):
                    retrieval_metadata['total_results'] = len(content)
                    
                    for item in content:
                        if isinstance(item, dict) and "text" in item:
                            all_results.append(item["text"])
                            
                            # Extract score if available
                            score = item.get("score", 0.0)
                            if isinstance(score, (int, float)):
                                scores.append(float(score))
                                if score >= 0.5:
                                    retrieval_metadata['high_confidence_results'] += 1
                    
                    # Calculate confidence metrics
                    if scores:
                        retrieval_metadata['avg_score'] = sum(scores) / len(scores)
                        retrieval_metadata['max_score'] = max(scores)
                        
                        # Determine confidence level
                        if retrieval_metadata['avg_score'] >= 0.6:
                            retrieval_metadata['confidence_level'] = 'high'
                        elif retrieval_metadata['avg_score'] >= 0.5:
                            retrieval_metadata['confidence_level'] = 'medium'
                        else:
                            retrieval_metadata['confidence_level'] = 'low'
                            
        except Exception as search_error:
            print(f"Knowledge base search failed: {search_error}")
        
        # Format results with confidence information
        if all_results:
            confidence_summary = (
                f"Knowledge Base Search Results:\n"
                f"• Found {retrieval_metadata['total_results']} relevant documents\n"
                f"• High confidence matches (≥0.5): {retrieval_metadata['high_confidence_results']}\n"
                f"• Average relevance score: {retrieval_metadata['avg_score']:.3f}\n"
                f"• Best match score: {retrieval_metadata['max_score']:.3f}\n"
                f"• Confidence level: {retrieval_metadata['confidence_level'].upper()}\n\n"
            )
            
            combined_result = confidence_summary + "\n\n".join(all_results)
            
            # Store both content and metadata
            tool_execution_results['knowledge_base_context'] = combined_result
            tool_execution_results['kb_metadata'] = retrieval_metadata
            
            print(f"Knowledge Base: {retrieval_metadata['total_results']} results, "
                  f"avg score {retrieval_metadata['avg_score']:.3f}, "
                  f"confidence: {retrieval_metadata['confidence_level']}")
            
            return combined_result
        else:
            no_results = f"No relevant documentation found for: {query}"
            tool_execution_results['knowledge_base_context'] = no_results
            tool_execution_results['kb_metadata'] = retrieval_metadata
            return no_results
            
    except Exception as e:
        error_msg = f"Error searching Knowledge Base: {str(e)}"
        print(f"ERROR: {error_msg}")
        tool_execution_results['knowledge_base_context'] = error_msg
        return error_msg

# Create the Strands Agent with model selection
if USE_SONNET_4:
    # Claude Sonnet 4 with Interleaved Thinking
    model = BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",  # Claude 4 Sonnet
        max_tokens=8192,
        temperature=1,  # Required to be 1 when thinking is enabled
        additional_request_fields={
            # Enable interleaved thinking beta feature
            "anthropic_beta": ["interleaved-thinking-2025-05-14"],
            # Configure reasoning parameters
            "reasoning_config": {
                "type": "enabled",  # Turn on thinking
                "budget_tokens": 3000  # Thinking token budget for complex analysis
            }
        }
    )
else:
    # Claude 3.7 Sonnet with thinking mode
    model = BedrockModel(
        model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        additional_request_fields={
            "thinking": {
                "type": "enabled",
                "budget_tokens": 2048,
            }
        }
    )

error_analysis_agent = Agent(
    model=model,
    system_prompt="""You are an expert automation error analyst for AWS Lambda failures.

    Use your thinking capability to reason through complex error scenarios step by step.
    
    Available tools provide:
    - fetch_source_code: Get exact Lambda source code from S3
    - search_knowledge_base: Documentation, best practices, error patterns
    - fetch_cloudwatch_logs: Full execution logs with stack traces
    
    Always use tools to gather context, then provide analysis with:
    - Root cause explanation based on evidence
    - Specific actionable recommendations
    - Relevant code context when available
    
    Format as enhanced error message. Be thorough but concise.""",
    tools=[fetch_source_code, search_knowledge_base, fetch_cloudwatch_logs]
)

def extract_lambda_name_from_event(event: Dict[str, Any]) -> str:
    """Extract and validate Lambda function name from EventBridge event"""
    try:
        # Try multiple possible locations for function name
        detail = event.get("detail", {})
        lambda_info = detail.get("lambda", {})
        
        # Primary: from lambda info in event detail
        function_name = lambda_info.get("functionName", "")
        
        # Fallback: from event source
        if not function_name:
            source = event.get("source", "")
            if "ams.automation.lambda." in source:
                function_name = source.split("ams.automation.lambda.")[-1]
        
        # Clean and validate
        if function_name:
            # Remove common AWS suffixes and clean the name
            clean_name = function_name.replace("-lambda", "").replace("_lambda", "")
            return clean_name.strip()
        
        return ""
        
    except Exception as e:
        print(f"Error extracting Lambda name: {e}")
        return ""

def calculate_analysis_confidence(tool_results: dict) -> dict:
    """Calculate overall confidence score based on available evidence and tool success"""
    confidence_factors = []
    confidence_score = 0.0
    
    # Knowledge Base confidence (0.0 - 0.4)
    kb_metadata = tool_results.get('kb_metadata', {})
    if kb_metadata.get('total_results', 0) > 0:
        kb_confidence = min(0.4, kb_metadata.get('avg_score', 0.0) * 0.8)
        confidence_score += kb_confidence
        confidence_factors.append(f"Knowledge Base: {kb_metadata.get('total_results', 0)} docs, avg score {kb_metadata.get('avg_score', 0.0):.3f}")
    
    # Source Code availability with method-specific confidence (0.0 - 0.3)
    source_code = tool_results.get('source_code', '')
    source_method = tool_results.get('source_code_method', 'Unknown')
    
    if source_code and 'Error fetching' not in source_code and 'No Python files found' not in source_code:
        # Adjust confidence based on retrieval method
        if source_method == 'S3 source bucket':
            confidence_score += 0.3  # Full confidence for S3 source
            confidence_factors.append("Source code retrieved successfully (S3 source bucket)")
        elif source_method == 'Lambda function ZIP':
            confidence_score += 0.25  # Slightly lower confidence for Lambda ZIP
            confidence_factors.append("Source code retrieved successfully (Lambda deployment package)")
        else:
            confidence_score += 0.2  # Lower confidence for unknown method
            confidence_factors.append("Source code retrieved successfully")
    elif 'Error fetching' in source_code or 'No Python files found' in source_code or source_method == 'Failed':
        confidence_factors.append("Source code retrieval failed - no files found")
    elif source_method == 'Exception':
        confidence_factors.append("Source code retrieval failed - exception occurred")
    
    # CloudWatch Logs quality (0.0 - 0.3)
    logs = tool_results.get('cloudwatch_logs', '')
    if logs and 'Error fetching' not in logs:
        if 'execution logs found' in logs.lower() or 'START RequestId' in logs:
            confidence_score += 0.3
            confidence_factors.append("Complete execution logs retrieved")
        else:
            confidence_score += 0.15
            confidence_factors.append("Partial logs retrieved")
    elif 'Error fetching' in logs:
        confidence_factors.append("CloudWatch logs retrieval failed")
    
    # Determine confidence level
    if confidence_score >= 0.8:
        confidence_level = 'very_high'
    elif confidence_score >= 0.6:
        confidence_level = 'high'
    elif confidence_score >= 0.4:
        confidence_level = 'medium'
    elif confidence_score >= 0.2:
        confidence_level = 'low'
    else:
        confidence_level = 'very_low'
    
    return {
        'confidence_score': round(confidence_score, 3),
        'confidence_level': confidence_level,
        'confidence_factors': confidence_factors,
        'evidence_quality': {
            'knowledge_base_score': kb_metadata.get('avg_score', 0.0),
            'knowledge_base_results': kb_metadata.get('total_results', 0),
            'source_code_available': 'source_code' in tool_results and 'Error fetching' not in tool_results.get('source_code', '') and 'No Python files found' not in tool_results.get('source_code', ''),
            'source_code_method': tool_results.get('source_code_method', 'Unknown'),
            'execution_logs_available': 'cloudwatch_logs' in tool_results and 'Error fetching' not in tool_results.get('cloudwatch_logs', '')
        }
    }

def extract_recommendations(response_str: str) -> list:
    """Extract recommendations from agent response"""
    recommendations = []
    lines = response_str.split('\n')
    
    for line in lines:
        line_stripped = line.strip()
        # Look for numbered or bulleted items
        if (line_stripped.startswith(('1.', '2.', '3.', '4.', '5.')) or 
            line_stripped.startswith(('•', '-', '*'))):
            
            # Clean up the recommendation
            import re
            recommendation = re.sub(r'^[•\-\*\d\.]+\s*', '', line_stripped)
            recommendation = re.sub(r'^\*\*[^*]+\*\*:?\s*', '', recommendation)
            
            if len(recommendation) > 10:
                recommendations.append(recommendation[:200])
    
    return recommendations[:5]  # Limit to 5

def extract_event_data(event: Dict[str, Any]) -> Dict[str, str]:
    """Extract essential information from EventBridge event"""
    try:
        detail = event.get("detail", {})
        error_info = detail.get("error", {})
        lambda_info = detail.get("lambda", {})
        
        return {
            "error_message": error_info.get("message", "Unknown error"),
            "stack_trace": error_info.get("debug", {}).get("stackTrace", ""),
            "function_name": extract_lambda_name_from_event(event),
            "log_group": lambda_info.get("logGroupName", ""),
            "log_stream": lambda_info.get("logStreamName", ""),
            "request_id": lambda_info.get("requestId", "")
        }
    except Exception as e:
        print(f"Error extracting event data: {e}")
        return {
            "error_message": "Failed to extract event data",
            "stack_trace": "",
            "function_name": "",
            "log_group": "",
            "log_stream": "",
            "request_id": ""
        }



def analyze_error(event: Dict[str, Any]) -> Dict[str, str]:
    """Main function called by egress_script.py to analyze automation errors"""
    
    # Start timing the analysis
    analysis_start_time = datetime.now(timezone.utc)
    
    # Reset global tool results for this analysis
    global tool_execution_results
    tool_execution_results = {}
    
    try:
        print(f"Starting Strands Agent error analysis...")
        
        # Extract event data
        data = extract_event_data(event)
        error_message = data["error_message"]
        stack_trace = data["stack_trace"]
        function_name = data["function_name"]
        log_group = data["log_group"]
        log_stream = data["log_stream"]
        request_id = data["request_id"]
        
        print(f"Analyzing error from Lambda: {function_name}")
        print(f"Request ID: {request_id}")
        
        # Build analysis prompt
        safe_error_message = error_message.replace('"', "'").replace('\n', ' ')[:200]
        
        analysis_prompt = f"""Analyze this automation error:
        
        ERROR: {safe_error_message}
        FUNCTION: {function_name}
        REQUEST ID: {request_id}
        LOGS: {log_group}/{log_stream}
        
        Use tools to gather context and provide:
        - Root cause analysis
        - Specific fix recommendations
        
        Keep response concise."""
        
        # Call the Strands Agent with validated data
        print(f"Calling Strands Agent with comprehensive context...")
        
        try:
            agent_response = error_analysis_agent(analysis_prompt)
            print(f"Agent completed successfully")
            
        except Exception as e:
            print(f"Agent analysis failed: {e}")
            # Return original error if agent fails
            agent_response = f"AGENT ANALYSIS FAILED: {error_message}\n\nError: {str(e)}"
        
        # Extract response text (simplified)
        if hasattr(agent_response, 'message') and isinstance(agent_response.message, dict):
            content = agent_response.message.get('content', [])
            response_str = ""
            for item in content:
                if isinstance(item, dict) and 'text' in item:
                    response_str += item['text'] + "\n"
            if not response_str.strip():
                response_str = str(agent_response.message)
        else:
            response_str = str(agent_response)
        
        # Fallback if response is too short
        if not response_str or len(response_str.strip()) < 50:
            response_str = f"Analysis failed: {error_message}"
        
        # Extract recommendations and calculate confidence
        recommendations = extract_recommendations(response_str)
        confidence_data = calculate_analysis_confidence(tool_execution_results)
        
        # Calculate analysis duration
        analysis_end_time = datetime.now(timezone.utc)
        analysis_duration = analysis_end_time - analysis_start_time
        duration_seconds = analysis_duration.total_seconds()
        duration_mm_ss = f"{int(duration_seconds // 60):02d}:{int(duration_seconds % 60):02d}"
        
        # Prepare analysis data for storage
        analysis_data = {
            'original_event': event,
            'agent_analysis': response_str,  # Changed from 'agent_response' to match DynamoDB
            'tools_used': list(tool_execution_results.keys()),
            'source_code': tool_execution_results.get('source_code', ''),
            'cloudwatch_logs': tool_execution_results.get('cloudwatch_logs', ''),
            'knowledge_base_context': tool_execution_results.get('knowledge_base_context', ''),
            'recommendations': recommendations,
            'error_message': error_message,
            'function_name': function_name,
            'request_id': request_id,
            'stack_trace': stack_trace,
            'log_group': log_group,
            'log_stream': log_stream,
            'analysis_timestamp': analysis_start_time.isoformat(),
            'analysis_duration_seconds': duration_seconds,
            'analysis_duration_mm_ss': duration_mm_ss,
            # Add confidence data
            'confidence_score': confidence_data['confidence_score'],
            'confidence_level': confidence_data['confidence_level'],
            'confidence_factors': confidence_data['confidence_factors'],
            'evidence_quality': confidence_data['evidence_quality']
        }
        
        print(f"Agent analysis completed for {function_name} ({len(response_str)} chars) in {duration_mm_ss}")
        print(f"Analysis confidence: {confidence_data['confidence_score']:.3f} ({confidence_data['confidence_level']})")
        
        # Store the complete analysis in DynamoDB
        try:
            store_result = store_analysis_result(analysis_data)
            print(f"Analysis stored: {store_result}")
        except Exception as store_error:
            print(f"Failed to store analysis: {store_error}")
        
        # Return both original error and AI analysis with confidence
        return {
            "error": error_message,
            "stack_trace": stack_trace,
            "agent_analysis": response_str,
            "confidence_score": confidence_data['confidence_score'],
            "confidence_level": confidence_data['confidence_level']
        }
        
    except Exception as e:
        error_msg = f"Error during Strands Agent analysis: {str(e)}"
        print(f"ERROR: {error_msg}")
        
        # Return original error message if agent fails
        original_error = event.get("detail", {}).get("error", {}).get("message", "Unknown error")
        return {
            "error": original_error,
            "agent_analysis": f"AI Analysis temporarily unavailable: {str(e)}"
        }

if __name__ == "__main__":
    # Test function for local development
    print("Strands Agent for Error Analysis - Ready")
    print("Use analyze_error(event) function to process automation failures")