import time
import boto3
import ipywidgets as widgets
import uuid
import pandas as pd
import numpy as np
import os
import shutil
import sqlite3
import functools
import requests
import pytz
import warnings
from IPython.display import Image, display
from botocore.config import Config
from typing import Annotated, Literal, Optional, Union
from typing_extensions import TypedDict
from bs4 import BeautifulSoup
from datetime import date, datetime
from typing import List, Dict, Any
import re
import json
import ast
from strands import Agent
import json
from typing import Any, Dict, Iterable, List, Tuple, Union


def extract_text_from_response(response_str):
    try:
        # First try to parse as JSON
        response_dict = json.loads(response_str)
    except json.JSONDecodeError:
        try:
            # If JSON fails, try ast.literal_eval
            response_dict = ast.literal_eval(response_str)
        except:
            return "Error parsing response"
    
    # Extract text from content
    try:
        return response_dict['content'][0]['text']
    except (KeyError, IndexError):
        return "Error extracting text"
        

def normalize_prompt(prompt) -> str:
    if isinstance(prompt, list):
        # assume list of dicts like [{"text": "..."}]
        texts = [p.get("text", "") for p in prompt if isinstance(p, dict)]
        return " ".join(t.strip() for t in texts if t)
    if isinstance(prompt, dict) and "text" in prompt:
        return prompt["text"].strip()
    if isinstance(prompt, str):
        return prompt.strip()
    return str(prompt).strip()


def extract_original_task(text: str) -> str | None:
    """
    Returns the text of 'Original Task' if present, else None.
    Works even if there are extra spaces/newlines and stops before
    'Inputs from previous nodes:' or a blank line.
    """
    pattern = re.compile(
        r"^Original\s*Task:\s*(.+?)(?=\n\s*\n|^\s*Inputs from previous nodes:|\Z)",
        re.IGNORECASE | re.DOTALL | re.MULTILINE
    )
    m = pattern.search(text)
    return m.group(1).strip() if m else None


def extract_task_and_plans(blob: str):
    # 1) Original Task
    m = re.search(
        r"Original Task:\s*(.+?)(?:\s*Inputs from previous nodes:|\Z)",
        blob, flags=re.DOTALL | re.IGNORECASE
    )
    original_task = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""

    # 2) content[0]['text'] — get the dict after "- Agent:" with a brace-balanced scan,
    #    parse it, then read content[0]['text']. Fallback to regex if parsing fails.
    evidence = ""

    agent_pos = blob.find("- Agent:")
    if agent_pos != -1:
        i = blob.find("{", agent_pos)
        if i != -1:
            depth, in_str, esc = 0, False, False
            quote = ""
            start = i
            end = -1
            while i < len(blob):
                ch = blob[i]
                if in_str:
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == quote:
                        in_str = False
                else:
                    if ch in ("'", '"'):
                        in_str, quote = True, ch
                    elif ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            end = i + 1
                            break
                i += 1

            if end != -1:
                agent_dict_str = blob[start:end]
                try:
                    agent = ast.literal_eval(agent_dict_str)
                    content = agent.get("content", [])
                    if isinstance(content, list) and content and isinstance(content[0], dict):
                        evidence = content[0].get("text", "")
                except Exception:
                    pass

    # Regex fallback if parsing failed
    if not evidence:
        m2 = re.search(
            r"'content'\s*:\s*\[\s*\{\s*'text'\s*:\s*'((?:\\'|[^'])*?)'",
            blob, flags=re.DOTALL
        )
        if m2:
            # minimally unescape \' -> '  (comment this out if you want the raw stored form)
            evidence = m2.group(1).replace("\\'", "'")

    return original_task, evidence



    

def _clean_text(s: str) -> str:
    # Remove literal backslash escapes and real control chars
    s = (s.replace('\\n', ' ')
           .replace('\\t', ' ')
           .replace('\\r', ' ')
           .replace('\n', ' ')
           .replace('\t', ' ')
           .replace('\r', ' '))
    s = re.sub(r'[\x00-\x1f\x7f]', ' ', s)   # other control chars
    s = s.strip(' \'"`,:')                   # trim common junk at ends
    s = re.sub(r'\s+', ' ', s)               # collapse whitespace
    return s

def sanitize_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    cleaned: Dict[str, Any] = {}
    for k, v in kwargs.items():
        # Clean key
        new_k = _clean_text(k) if isinstance(k, str) else k
        # Clean value (only strings; leave lists/dicts as-is)
        if isinstance(v, str):
            new_v = _clean_text(v)
        else:
            new_v = v
        cleaned[new_k] = new_v
    return cleaned

ContextType = Union[Dict[str, Dict[str, Any]], List[Tuple[str, Dict[str, Any]]]]

def _normalize_context(ctx: ContextType) -> List[Tuple[str, Dict[str, Any]]]:
    return list(ctx.items()) if isinstance(ctx, dict) else list(ctx)

def _parse_results(r: Any) -> Any:
    """Parse JSON-looking strings; return dict/list, else None (we only traverse structured)."""
    if isinstance(r, (dict, list)):
        return r
    if isinstance(r, str):
        s = r.strip()
        if s and s[0] in "{[":
            try:
                return json.loads(s)
            except Exception:
                return None
    return None

def _iter_hits(obj: Any, keys: List[str]) -> Iterable[Any]:
    """Yield any values whose dict key is in `keys` (recursive)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in keys:
                yield v
            yield from _iter_hits(v, keys)
    elif isinstance(obj, list):
        for it in obj:
            yield from _iter_hits(it, keys)

def resolve_kwargs_from_dict(
    kwargs: Dict[str, Any],
    context_dict: ContextType,
    *,
    prefer_latest: bool = True
) -> Dict[str, Any]:
    """
    Update only the keys present in `kwargs` by searching all evidences' `results`.
    - For 'passengers', also search 'saved_passengers'.
    - Latest evidence takes precedence.
    - Leaves values unchanged if not found.
    """
    items = _normalize_context(context_dict)
    if prefer_latest:
        items = list(reversed(items))  # search latest-first

    out = dict(kwargs)  # do not add new keys

    for key in kwargs.keys():
        search_keys = [key]
        if key == "passengers":
            search_keys.append("saved_passengers")

        found = None
        for _, rec in items:
            obj = _parse_results(rec.get("results"))
            if obj is None:
                continue
            # first hit in this evidence wins; since we iterate latest-first,
            # the first evidence that has the key wins overall
            for val in _iter_hits(obj, search_keys):
                found = val
                break
            if found is not None:
                break

        if found is not None:
            # small normalization: if passengers is a dict, wrap as a list
            if key == "passengers" and isinstance(found, dict):
                found = [found]
            out[key] = found

    return out



#  function to parse tool definitions
def parse_tool_definitions(tool_definitions):
    def smart_split(param_str):
        """Split parameters by comma, ignoring commas inside nested brackets."""
        parts = []
        current = []
        depth = 0
        for char in param_str:
            if char == ',' and depth == 0:
                parts.append(''.join(current).strip())
                current = []
            else:
                if char in '[({':
                    depth += 1
                elif char in '])}':
                    depth -= 1
                current.append(char)
        if current:
            parts.append(''.join(current).strip())
        return parts

    tool_params = {}
    for line in tool_definitions.strip().split('\n'):
        line = line.strip()
        if not line.startswith('*'):
            continue
        line = line.lstrip('*').strip()

        if '->' not in line:
            continue

        signature, _ = line.split('->', 1)
        if '[' not in signature or ']' not in signature:
            continue

        func_name = signature.split('[', 1)[0].strip()
        param_block = signature.split('[', 1)[1].rsplit(']', 1)[0]

        param_dict = {}
        if param_block:
            for param in smart_split(param_block):
                if ': ' in param:
                    param_name, param_type = param.split(': ', 1)
                    param_dict[param_name.strip()] = param_type.strip()

        tool_params[func_name] = param_dict

    return tool_params


# Parse the tool definitions
tool_params = parse_tool_definitions("""
* calculate[expression: str] -> str
* get_reservation_details[reservation_id: str] -> str
* update_reservation_flights[reservation_id: str, cabin: str, flights: List[Dict[str, Any]], payment_id: str] -> str
* search_onestop_flight[origin: str, destination: str, date: str] -> str
* send_certificate[user_id: str, amount: int] -> str
* cancel_reservation[reservation_id: str] -> str
* search_direct_flight[origin: str, destination: str, date: str] -> str
* get_user_details[user_id: str] -> str
* list_all_airports[] -> str
* book_reservation[user_id: str, origin: str, destination: str, flight_type: str, cabin: str, flights: List[Dict[str, Any]], passengers: List[Dict[str, Any]], payment_methods: List[Dict[str, Any]], total_baggages: int, nonfree_baggages: int, insurance: str] -> str
* think[thought: str] -> str
* transfer_to_human_agents[summary: str] -> str
* update_reservation_passengers[reservation_id: str, passengers: List[Dict[str, Any]]] -> str
* update_reservation_baggages[reservation_id: str, total_baggages: int, nonfree_baggages: int, payment_id: str] -> str
""")

# resolve arguments function
def resolve_arguments(tool_name, kwargs, evidence, context, bedrock_model_taubench):
    # Get parameter definitions for this tool
    
    params_def = tool_params.get(tool_name, {})
    
    # Resolve arguments from context if needed
    for key, value in kwargs.items():
        # Get expected type for this parameter
        expected_type = params_def.get(key, "str")
        
        # Build a type-specific system prompt
        type_instructions = ""
        format_example = ""
        
        if expected_type == "str":
            if key in ["origin", "destination"]:
                type_instructions = "Return only the 3-letter airport code (e.g., JFK, LAX, SEA)."
                format_example = "Example: For 'New York', return 'JFK' or 'LGA'."
            elif key == "date":
                type_instructions = "Return the date in YYYY-MM-DD format."
                format_example = "Example: For 'May 20', return '2024-05-20'."
            elif key == "flight_type":
                type_instructions = "Return only 'one_way' or 'two_way'."
                format_example = "Example: For 'one way trip', return 'one_way'."
            elif key == "cabin":
                type_instructions = "Return only 'basic_economy', 'economy', 'premium_economy', 'business', or 'first'."
                format_example = "Example: For 'economy class', return 'economy'."
            elif key == "insurance":
                type_instructions = "Return only 'yes' or 'no'."
                format_example = "Example: For 'no insurance', return 'no'."
                
        elif "List" in expected_type:
            type_instructions = f"Return a valid JSON array matching {expected_type}."
            if key == "flights":
                format_example = """Note: This is just an example format. Return an array of flight objects with the appropriate data based on the actual query results:
[{"flight_number": "HAT123", "origin": "LAX", "destination": "ORD", "scheduled_departure_time_est": "08:15:00", "scheduled_arrival_time_est": "14:30:00",
"status": "available", "available_seats": {"basic_economy": 24, "economy": 18, "business": 6}, 
"prices": {"basic_economy": 89, "economy": 159, "business": 349}}, 
{"flight_number": "HAT456", "origin": "SFO", "destination": "DFW", "scheduled_departure_time_est": "11:45:00", "scheduled_arrival_time_est": "17:20:00", 
"status": "limited", "available_seats": {"basic_economy": 5, "economy": 2, "business": 1}, 
"prices": {"basic_economy": 145, "economy": 210, "business": 420}}]"""
            elif key == "passengers":
                format_example = """Note: This is just an example format. Return an array of passenger objects with the actual passenger information:
[
  {
    "first_name": "John",
    "last_name": "Smith",
    "dob": "1985-06-15"
  },
  {
    "first_name": "Emma",
    "last_name": "Garcia",
    "dob": "1992-03-22"
  }
]"""
            elif key == "payment_methods":
                format_example = """Note: This is just an example format. Return an array of ALL payment method objects that apply to the transaction. Include all available payment types (credit cards, gift certificates, loyalty points, etc.) as required by the customer:
[
  {
    "payment_id": "credit_card_1234",
    "amount": 350.75,
    "type": "credit_card"
  },
  {
    "payment_id": "gift_certificate_789",
    "amount": 100.00,
    "type": "gift_certificate"
  },
  {
    "payment_id": "loyalty_points_456",
    "amount": 50.00,
    "type": "loyalty_points"
  }
]"""
                
        elif expected_type == "int":
            type_instructions = "Return only a number with no text or symbols."
            format_example = "Example: For '3 bags', return '3'."
            
        # Create the system prompt
        system_prompt = f"""Extract the value for the parameter '{key}' from the given context. Analyze both the User Query and the Evidence Context to extract the correct value for the key.
{type_instructions}
{format_example}
The parameter should be of type: {expected_type}
Return ONLY the value and nothing else, no explanation or thinking."""

        # Resolve the parameter
        param_resolver = Agent(
            model=bedrock_model_taubench,
            system_prompt=system_prompt
        )
        
        resolved_value = param_resolver(f"Context:\n{context}\n\n Extract value for parameter: {key}")
        resolved_value = str(resolved_value).strip()
        
        # Handle type conversion based on expected type
        try:
            if "List" in expected_type:
                # Ensure JSON arrays are properly formatted
                #if not (resolved_value.startswith('[') and resolved_value.endswith(']')):
                #    resolved_value = f"[{resolved_value}]"
                kwargs[key] = json.loads(resolved_value)
                print(f"DEBUG: Parsed List parameter {key}: {kwargs[key]}")
            elif expected_type == "int":
                # Strip any non-numeric characters and convert to int
                numeric_value = ''.join(c for c in resolved_value if c.isdigit())
                kwargs[key] = int(numeric_value) if numeric_value else 0
                print(f"DEBUG: Converted to int {key}: {kwargs[key]}")            
            else:
                kwargs[key] = resolved_value
                print(f"DEBUG: Resolved string {key}: {kwargs[key]}")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"DEBUG: Error converting {key} to {expected_type}: {e}")
            kwargs[key] = resolved_value  # Keep as string if conversion fails
            

    
    return kwargs