#!/usr/bin/env python3

import os
import json
import boto3
import base64
from pypdf import PdfReader
from strands import tool

@tool
def process_document(file_path: str) -> str:
    """
    Process a medical document (PDF or image) and extract its content using Amazon Bedrock.
    
    Args:
        file_path: Path to the document file (PDF or image)
        
    Returns:
        Extracted text content from the document
    """
    if not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"})
    
    file_extension = os.path.splitext(file_path)[1].lower()
    
    try:
        # Use Bedrock for all document types
        if file_extension == '.pdf':
            # For PDFs, try Bedrock first, then fall back to traditional PDF extraction
            try:
                return _use_bedrock_for_document(file_path)
            except Exception as e:
                print(f"Bedrock processing failed, falling back to PDF extraction: {str(e)}")
                return _process_pdf_traditional(file_path)
        
        # Process image files with Bedrock
        elif file_extension in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            return _use_bedrock_for_document(file_path)
        
        else:
            return json.dumps({"error": f"Unsupported file format: {file_extension}"})
            
    except Exception as e:
        return json.dumps({"error": f"Error processing document: {str(e)}"})

def _process_pdf_traditional(file_path: str) -> str:
    """Extract text from a PDF file using PyPDF."""
    try:
        # Extract text directly from PDF
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        # If text extraction yields meaningful content, return it
        if len(text.strip()) > 50:
            return text
        
        # If minimal text was extracted, the PDF might be scanned/image-based
        # In this case, we can't extract text using traditional methods
        return json.dumps({"error": "PDF appears to be image-based and requires Bedrock for processing"})
        
    except Exception as e:
        return json.dumps({"error": f"Error processing PDF: {str(e)}"})

def _use_bedrock_for_document(file_path: str) -> str:
    """Use Amazon Bedrock for document processing."""
    try:
        # Initialize Bedrock client
        bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        
        # Read file as base64
        with open(file_path, 'rb') as file:
            file_bytes = file.read()
            base64_data = base64.b64encode(file_bytes).decode('utf-8')
        
        # Determine media type based on file extension
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == '.pdf':
            media_type = 'application/pdf'
        elif file_extension == '.png':
            media_type = 'image/png'
        elif file_extension in ['.jpg', '.jpeg']:
            media_type = 'image/jpeg'
        elif file_extension == '.tiff':
            media_type = 'image/tiff'
        elif file_extension == '.bmp':
            media_type = 'image/bmp'
        else:
            media_type = 'application/octet-stream'
        
        # Prepare request for Claude model
        model_id = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64_data
                            }
                        },
                        {
                            "type": "text",
                            "text": "Extract all text content from this medical document. Preserve the formatting as much as possible. Include all medical terms, diagnoses, medications, and treatments. Be thorough and capture all details from the document."
                        }
                    ]
                }
            ]
        }
        
        # Invoke Bedrock model
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read().decode('utf-8'))
        extracted_text = response_body['content'][0]['text']
        
        return extracted_text
        
    except Exception as e:
        raise Exception(f"Error using Bedrock for document processing: {str(e)}")
