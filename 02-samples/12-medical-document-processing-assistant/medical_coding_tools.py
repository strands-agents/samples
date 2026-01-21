#!/usr/bin/env python3

import os
import json
import requests
from typing import List, Dict, Any, Optional
import boto3
from strands import tool

# Base URLs for medical terminology APIs
ICD10_API_BASE_URL = "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search"
RXNORM_API_BASE_URL = "https://rxnav.nlm.nih.gov/REST/rxcui"
RXNORM_INFO_API_BASE_URL = "https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/allrelated"
SNOMED_API_BASE_URL = "https://browser.ihtsdotools.org/snowstorm/snomed-ct/MAIN/concepts"
SNOMED_BROWSER_URL = "https://browser.ihtsdotools.org/?perspective=full&edition=MAIN/SNOMEDCT-US/2025-03-01&languages=en"

@tool
def get_icd(diagnosis: str) -> str:
    """
    Get ICD-10 codes for a given diagnosis using the NLM Clinical Tables API.
    
    Args:
        diagnosis: The medical diagnosis to look up
        
    Returns:
        JSON string containing matching ICD-10 codes and descriptions
    """
    try:
        # Use the NLM Clinical Tables API (no authentication required)
        return _get_icd_from_api(diagnosis)
    except Exception as e:
        # Fallback to Bedrock for code lookup if API fails
        try:
            return _get_medical_code_from_bedrock(
                diagnosis, 
                "ICD-10", 
                "Find the most appropriate ICD-10 codes for this diagnosis"
            )
        except Exception as inner_e:
            return json.dumps({
                "error": f"Error retrieving ICD-10 codes: {str(e)}. Fallback error: {str(inner_e)}",
                "diagnosis": diagnosis
            })

@tool
def get_rx(medication: str) -> str:
    """
    Get RxNorm codes for a given medication using the NLM RxNav API.
    
    Args:
        medication: The medication name to look up
        
    Returns:
        JSON string containing matching RxNorm codes and information
    """
    try:
        # Use the NLM RxNav API (no authentication required)
        return _get_rx_from_api(medication)
    except Exception as e:
        # Fallback to Bedrock for code lookup if API fails
        try:
            return _get_medical_code_from_bedrock(
                medication, 
                "RxNorm", 
                "Find the most appropriate RxNorm codes for this medication"
            )
        except Exception as inner_e:
            return json.dumps({
                "error": f"Error retrieving RxNorm codes: {str(e)}. Fallback error: {str(inner_e)}",
                "medication": medication
            })

@tool
def get_snomed(treatment: str) -> str:
    """
    Get SNOMED CT codes for a given treatment or procedure using the SNOMED CT browser API.
    
    Args:
        treatment: The medical treatment or procedure to look up
        
    Returns:
        JSON string containing matching SNOMED CT codes and descriptions
    """
    try:
        # Use the SNOMED CT browser API
        return _get_snomed_from_api(treatment)
    except Exception as e:
        # Fallback to Bedrock for code lookup if API fails
        try:
            return _get_medical_code_from_bedrock(
                treatment, 
                "SNOMED CT", 
                "Find the most appropriate SNOMED CT codes for this treatment or procedure"
            )
        except Exception as inner_e:
            return json.dumps({
                "error": f"Error retrieving SNOMED CT codes: {str(e)}. Fallback error: {str(inner_e)}",
                "treatment": treatment
            })

@tool
def link_icd(clinical_text: str) -> str:
    """
    Extract diagnoses from clinical text and link them to ICD-10 codes.
    
    Args:
        clinical_text: The clinical text to analyze
        
    Returns:
        JSON string containing extracted diagnoses with their ICD-10 codes
    """
    try:
        # Use Bedrock to extract diagnoses and link to ICD-10 codes
        prompt = f"""
        Extract all diagnoses from the following clinical text and link them to the most appropriate ICD-10 codes.
        For each diagnosis, provide:
        1. The diagnosis as mentioned in the text
        2. The ICD-10 code
        3. The official ICD-10 description
        4. A confidence score (95% for high confidence, lower for less certain matches)
        
        Clinical text:
        {clinical_text}
        
        Format the output as a JSON array of diagnosis objects with the exact format:
        [
            {{
                "diagnosis": "Atrial fibrillation",
                "ICD10_code": "I48.0",
                "description": "Paroxysmal atrial fibrillation",
                "confidence_score": "95%"
            }},
            ...
        ]
        """
        
        return _get_structured_data_from_bedrock(prompt, "diagnoses")
    except Exception as e:
        return json.dumps([{
            "diagnosis": "Error",
            "ICD10_code": "Error",
            "error": f"Error linking diagnoses to ICD-10 codes: {str(e)}",
            "confidence_score": "0%"
        }])

@tool
def link_rx(clinical_text: str) -> str:
    """
    Extract medications from clinical text and link them to RxNorm codes.
    
    Args:
        clinical_text: The clinical text to analyze
        
    Returns:
        JSON string containing extracted medications with their RxNorm codes
    """
    try:
        # Use Bedrock to extract medications and link to RxNorm codes
        prompt = f"""
        Extract all medications from the following clinical text and link them to the most appropriate RxNorm codes.
        For each medication, provide:
        1. The medication name as mentioned in the text
        2. The RxNorm code
        3. The standard RxNorm name/description
        4. The dosage if specified
        5. The frequency if specified
        6. A confidence score (95% for high confidence, lower for less certain matches)
        
        Clinical text:
        {clinical_text}
        
        Format the output as a JSON array of medication objects with the exact format:
        [
            {{
                "medication": "Topamax",
                "RxNorm_code": "36926",
                "description": "Topiramate 50 MG Oral Tablet",
                "dosage": "50 mg",
                "frequency": "daily",
                "confidence_score": "95%"
            }},
            ...
        ]
        """
        
        return _get_structured_data_from_bedrock(prompt, "medications")
    except Exception as e:
        return json.dumps([{
            "medication": "Error",
            "RxNorm_code": "Error",
            "error": f"Error linking medications to RxNorm codes: {str(e)}",
            "confidence_score": "0%"
        }])

@tool
def link_snomed(clinical_text: str) -> str:
    """
    Extract treatments and procedures from clinical text and link them to SNOMED CT codes.
    
    Args:
        clinical_text: The clinical text to analyze
        
    Returns:
        JSON string containing extracted treatments with their SNOMED CT codes
    """
    try:
        # Use Bedrock to extract treatments and link to SNOMED CT codes
        prompt = f"""
        Extract all treatments, procedures, and clinical actions from the following clinical text and link them to the most appropriate SNOMED CT codes.
        For each treatment or procedure, provide:
        1. The treatment/procedure as mentioned in the text
        2. The SNOMED CT code
        3. The official SNOMED CT description
        4. A confidence score (95% for high confidence, lower for less certain matches)
        
        Clinical text:
        {clinical_text}
        
        Format the output as a JSON array of procedure objects with the exact format:
        [
            {{
                "procedure": "Referral to neurologist",
                "SNOMED_code": "306206005",
                "description": "Referral to neurology service",
                "confidence_score": "95%"
            }},
            ...
        ]
        """
        
        return _get_structured_data_from_bedrock(prompt, "treatments")
    except Exception as e:
        return json.dumps([{
            "procedure": "Error",
            "SNOMED_code": "Error",
            "error": f"Error linking treatments to SNOMED CT codes: {str(e)}",
            "confidence_score": "0%"
        }])

def _get_icd_from_api(diagnosis: str, api_key: str = None) -> str:
    """
    Query NLM Clinical Tables API for ICD-10 codes.
    
    API Documentation: https://clinicaltables.nlm.nih.gov/apidoc/icd10cm/v3/doc.html
    """
    params = {
        "terms": diagnosis,
        "sf": "code,name",
        "df": "code,name",
        "maxResults": 5
    }
    
    # Note: This API doesn't require authentication for basic usage
    response = requests.get(ICD10_API_BASE_URL, params=params)
    
    if response.status_code == 200:
        data = response.json()
        results = []
        
        # The API returns data in the format [total, abbreviation, items_json, codes]
        # where codes is a list of codes and items_json contains descriptions
        if len(data) >= 4:
            codes = data[3]  # List of codes
            descriptions = data[2]  # List of descriptions
            
            for i, code in enumerate(codes):
                if i < len(descriptions):
                    # Calculate confidence score - higher for earlier results
                    confidence_score = f"{max(95 - (i * 5), 70)}%"
                    
                    results.append({
                        "diagnosis": diagnosis,
                        "ICD10_code": code,
                        "description": descriptions[i],
                        "confidence_score": confidence_score
                    })
        
        return json.dumps(results)
    else:
        return json.dumps([{
            "diagnosis": diagnosis,
            "error": f"API error: {response.status_code}",
            "confidence_score": "0%"
        }])

def _get_rx_from_api(medication: str, api_key: str = None) -> str:
    """
    Query RxNav API for RxNorm codes.
    
    API Documentation: https://lhncbc.nlm.nih.gov/RxNav/APIs/RxNormAPIs.html
    """
    # Step 1: Find RxCUI for the medication name
    params = {
        "name": medication
    }
    
    # RxNav API doesn't require authentication
    response = requests.get(f"{RXNORM_API_BASE_URL}", params=params)
    
    if response.status_code != 200:
        return json.dumps([{
            "medication": medication,
            "error": f"API error: {response.status_code}",
            "confidence_score": "0%"
        }])
    
    # Parse the XML response
    import xml.etree.ElementTree as ET
    root = ET.fromstring(response.content)
    
    # Extract RxCUI values
    rxcui_elements = root.findall(".//rxnormId")
    if not rxcui_elements:
        return json.dumps([{
            "medication": medication,
            "RxNorm_code": "Not found",
            "confidence_score": "0%"
        }])
    
    results = []
    
    # For each RxCUI, get additional information
    for i, rxcui_element in enumerate(rxcui_elements[:3]):  # Limit to first 3 results
        rxcui = rxcui_element.text
        
        # Step 2: Get related information for this RxCUI
        info_url = RXNORM_INFO_API_BASE_URL.format(rxcui=rxcui)
        info_response = requests.get(info_url)
        
        if info_response.status_code == 200:
            info_root = ET.fromstring(info_response.content)
            
            # Extract concept information
            concept_name = ""
            concept_elements = info_root.findall(".//conceptProperties")
            for concept in concept_elements:
                name_element = concept.find("name")
                tty_element = concept.find("tty")  # Term Type
                
                if name_element is not None and tty_element is not None:
                    # Prioritize SCD (Semantic Clinical Drug) or IN (Ingredient) term types
                    if tty_element.text in ["SCD", "IN", "BN"]:
                        concept_name = name_element.text
                        break
            
            # If we didn't find a preferred term type, use the first name
            if not concept_name and concept_elements and concept_elements[0].find("name") is not None:
                concept_name = concept_elements[0].find("name").text
            
            # Calculate confidence score - higher for earlier results
            confidence_score = f"{max(95 - (i * 5), 70)}%"
            
            results.append({
                "medication": medication,
                "RxNorm_code": rxcui,
                "description": concept_name or medication,
                "confidence_score": confidence_score
            })
    
    return json.dumps(results)

def _get_snomed_from_api(treatment: str, api_key: str = None) -> str:
    """
    Query SNOMED CT browser API for SNOMED CT codes.
    
    Uses the Snowstorm terminology server API that powers the SNOMED CT browser.
    """
    # The Snowstorm API endpoint for concept search
    search_url = f"{SNOMED_API_BASE_URL}/search"
    
    params = {
        "term": treatment,
        "activeFilter": True,
        "offset": 0,
        "limit": 5,
        # US Edition
        "branch": "MAIN/SNOMEDCT-US",
        # English language
        "language": "en",
        # Return FSN (Fully Specified Name) and PT (Preferred Term)
        "returnIdField": True,
        "returnFsnField": True,
        "returnPtField": True
    }
    
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    try:
        response = requests.get(search_url, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            if "items" in data and len(data["items"]) > 0:
                for i, item in enumerate(data["items"]):
                    concept_id = item.get("conceptId")
                    
                    # Get the Fully Specified Name (FSN)
                    fsn = item.get("fsn", {}).get("term", "")
                    
                    # Get the Preferred Term (PT)
                    pt = item.get("pt", {}).get("term", "")
                    
                    # Calculate confidence score - higher for earlier results
                    confidence_score = f"{max(95 - (i * 5), 70)}%"
                    
                    results.append({
                        "procedure": treatment,
                        "SNOMED_code": concept_id,
                        "description": pt or fsn,
                        "confidence_score": confidence_score
                    })
                
                return json.dumps(results)
            else:
                return json.dumps([{
                    "procedure": treatment,
                    "SNOMED_code": "Not found",
                    "confidence_score": "0%"
                }])
        else:
            return json.dumps([{
                "procedure": treatment,
                "error": f"API error: {response.status_code}",
                "confidence_score": "0%"
            }])
    except Exception as e:
        return json.dumps([{
            "procedure": treatment,
            "error": f"Error querying SNOMED CT API: {str(e)}",
            "confidence_score": "0%"
        }])

def _get_medical_code_from_bedrock(term: str, code_system: str, instruction: str) -> str:
    """Use Amazon Bedrock to look up medical codes."""
    try:
        # Initialize Bedrock client
        bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        
        # Prepare request for Claude model
        model_id = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
        
        # Adjust prompt based on code system
        if code_system == "ICD-10":
            code_field = "ICD10_code"
            term_field = "diagnosis"
        elif code_system == "RxNorm":
            code_field = "RxNorm_code"
            term_field = "medication"
        else:  # SNOMED CT
            code_field = "SNOMED_code"
            term_field = "procedure"
        
        prompt = f"""
        {instruction}: "{term}"
        
        Return the result in this exact JSON format:
        {{
            "{term_field}": "The exact term provided",
            "{code_field}": "The code",
            "description": "The official description",
            "confidence_score": "95%"
        }}
        
        If multiple codes are possible, return an array of JSON objects in the above format, with decreasing confidence scores (95%, 90%, 85%, etc.).
        """
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
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
        result = response_body['content'][0]['text']
        
        # Extract JSON from response if needed
        import re
        json_match = re.search(r'```json\n(.*?)\n```', result, re.DOTALL)
        if json_match:
            result = json_match.group(1)
        
        # Ensure result is valid JSON
        try:
            parsed_result = json.loads(result)
            # If it's not a list, convert to a list with one item
            if not isinstance(parsed_result, list):
                parsed_result = [parsed_result]
            return json.dumps(parsed_result)
        except:
            # If not valid JSON, create a fallback response
            return json.dumps([{
                term_field: term,
                code_field: "Unknown",
                "description": "Could not determine code",
                "confidence_score": "0%"
            }])
            
    except Exception as e:
        if code_system == "ICD-10":
            code_field = "ICD10_code"
            term_field = "diagnosis"
        elif code_system == "RxNorm":
            code_field = "RxNorm_code"
            term_field = "medication"
        else:  # SNOMED CT
            code_field = "SNOMED_code"
            term_field = "procedure"
            
        return json.dumps([{
            term_field: term,
            code_field: "Error",
            "error": f"Error using Bedrock for code lookup: {str(e)}",
            "confidence_score": "0%"
        }])

def _get_structured_data_from_bedrock(prompt: str, data_type: str) -> str:
    """Use Amazon Bedrock to extract structured data from clinical text."""
    try:
        # Initialize Bedrock client
        bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        
        # Prepare request for Claude model
        model_id = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
        
        # Modify prompt based on data type to ensure consistent output format
        if "diagnoses" in data_type:
            prompt += """
            Each diagnosis object should have this exact format:
            {
                "diagnosis": "The diagnosis as mentioned in the text",
                "ICD10_code": "The ICD-10 code",
                "description": "The official ICD-10 description",
                "confidence_score": "95%"
            }
            """
        elif "medications" in data_type:
            prompt += """
            Each medication object should have this exact format:
            {
                "medication": "The medication name as mentioned in the text",
                "RxNorm_code": "The RxNorm code",
                "description": "The standard RxNorm name",
                "dosage": "The dosage if specified (or null)",
                "frequency": "The frequency if specified (or null)",
                "confidence_score": "95%"
            }
            """
        elif "treatments" in data_type or "procedures" in data_type:
            prompt += """
            Each treatment/procedure object should have this exact format:
            {
                "procedure": "The treatment/procedure as mentioned in the text",
                "SNOMED_code": "The SNOMED CT code",
                "description": "The official SNOMED CT description",
                "confidence_score": "95%"
            }
            """
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
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
        result = response_body['content'][0]['text']
        
        # Extract JSON from response if needed
        import re
        json_match = re.search(r'```json\n(.*?)\n```', result, re.DOTALL)
        if json_match:
            result = json_match.group(1)
        
        # Ensure result is valid JSON
        try:
            parsed_result = json.loads(result)
            return result
        except:
            # If not valid JSON, create a fallback response
            if "diagnoses" in data_type:
                return json.dumps([{
                    "diagnosis": "Could not extract diagnoses",
                    "ICD10_code": "Unknown",
                    "description": "Error parsing response",
                    "confidence_score": "0%"
                }])
            elif "medications" in data_type:
                return json.dumps([{
                    "medication": "Could not extract medications",
                    "RxNorm_code": "Unknown",
                    "description": "Error parsing response",
                    "confidence_score": "0%"
                }])
            else:  # treatments/procedures
                return json.dumps([{
                    "procedure": "Could not extract procedures",
                    "SNOMED_code": "Unknown",
                    "description": "Error parsing response",
                    "confidence_score": "0%"
                }])
            
    except Exception as e:
        # Create appropriate error response based on data type
        if "diagnoses" in data_type:
            return json.dumps([{
                "diagnosis": "Error",
                "ICD10_code": "Error",
                "error": f"Error extracting structured data: {str(e)}",
                "confidence_score": "0%"
            }])
        elif "medications" in data_type:
            return json.dumps([{
                "medication": "Error",
                "RxNorm_code": "Error",
                "error": f"Error extracting structured data: {str(e)}",
                "confidence_score": "0%"
            }])
        else:  # treatments/procedures
            return json.dumps([{
                "procedure": "Error",
                "SNOMED_code": "Error",
                "error": f"Error extracting structured data: {str(e)}",
                "confidence_score": "0%"
            }])
