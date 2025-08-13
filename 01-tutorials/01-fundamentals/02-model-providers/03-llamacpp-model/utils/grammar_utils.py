"""
Grammar and sampling utilities for the LlamaCpp demo notebook.

This module contains functions for demonstrating grammar constraints,
testing different sampling strategies, and working with structured output.
"""

import json
import time
from typing import Dict, List, Any, Type

from pydantic import BaseModel
from strands import Agent
from strands.models.llamacpp import LlamaCppModel


def demonstrate_grammar_constraint(grammar: str, prompt: str, description: str,
                                 base_url: str = "http://localhost:8080",
                                 temperature: float = 0.1,
                                 max_tokens: int = 50) -> str:
    """
    Demonstrate a specific grammar constraint with the LlamaCpp model.
    
    Args:
        grammar: GBNF grammar string defining allowed outputs
        prompt: Input prompt for the model
        description: Human-readable description of the grammar constraint
        base_url: Base URL for the LlamaCpp server
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
    
    Returns:
        Model response constrained by the grammar
    """
    print("=" * 60)
    print(f"{description}")
    print(f"Grammar: {grammar}")
    print(f"Prompt: {prompt}")
    print("-" * 60)
    
    # Create model with grammar constraint
    # Ensure base_url doesn't have /v1 suffix to avoid double /v1 in URL
    clean_base_url = base_url.rstrip('/').replace('/v1', '')
    model = LlamaCppModel(
        base_url=clean_base_url,
        params={"temperature": temperature, "max_tokens": max_tokens}
    )
    
    model.use_grammar_constraint(grammar)
    agent = Agent(model=model)
    
    response = agent(prompt)
    
    # Extract text from response
    if hasattr(response, 'message') and 'content' in response.message:
        text_content = ""
        for content_block in response.message['content']:
            if 'text' in content_block:
                text_content += content_block['text']
        response_text = text_content.strip()
    else:
        response_text = str(response)
    
    print(f"Response: {response_text}")
    print("=" * 60)
    return response_text


def get_predefined_grammars() -> Dict[str, Dict[str, str]]:
    """
    Get a collection of predefined GBNF grammars for common use cases.
    
    Returns:
        Dictionary mapping grammar names to grammar definitions and descriptions
    """
    return {
        "yes_no": {
            "grammar": 'root ::= "yes" | "no" | "Yes" | "No"',
            "description": "Yes/No responses only",
            "example_prompt": "Is Python a compiled language?"
        },
        "number_1_10": {
            "grammar": 'root ::= [1-9] | "10"',
            "description": "Numbers from 1 to 10",
            "example_prompt": "On a scale of 1-10, how useful is machine learning?"
        },
        "multiple_choice": {
            "grammar": 'root ::= "A" | "B" | "C" | "D"',
            "description": "Multiple choice answers (A-D)",
            "example_prompt": "What is 2+2? A) 3, B) 4, C) 5, D) 6. Answer:"
        },
        "simple_json": {
            "grammar": '''root ::= "{" ws "\\"name\\"" ws ":" ws string ws "," ws "\\"age\\"" ws ":" ws number ws "}"
string ::= "\\"" [^"]* "\\""
number ::= [0-9]+
ws ::= [ \\t\\n]*''',
            "description": "Simple JSON with name and age",
            "example_prompt": "Generate a person with name and age in JSON:"
        },
        "color_names": {
            "grammar": 'root ::= "red" | "blue" | "green" | "yellow" | "purple" | "orange" | "black" | "white"',
            "description": "Basic color names only",
            "example_prompt": "What color is the sky?"
        },
        "email_format": {
            "grammar": '''root ::= username "@" domain "." tld
username ::= [a-zA-Z0-9_]+ 
domain ::= [a-zA-Z0-9]+ 
tld ::= "com" | "org" | "net" | "edu"''',
            "description": "Simple email format",
            "example_prompt": "Generate a sample email address:"
        }
    }


def test_sampling_strategy(params: Dict[str, Any], name: str, prompt: str,
                          base_url: str = "http://localhost:8080") -> tuple[str, float]:
    """
    Test a specific sampling strategy with the LlamaCpp model.
    
    Args:
        params: Dictionary of sampling parameters
        name: Human-readable name for the strategy
        prompt: Input prompt for testing
        base_url: Base URL for the LlamaCpp server
    
    Returns:
        Tuple of (response_text, elapsed_time)
    """
    print("\n" + "="*60)
    print(f"{name}")
    print(f"Parameters: {json.dumps(params, indent=2)}")
    print("-" * 60)
    
    # Ensure base_url doesn't have /v1 suffix to avoid double /v1 in URL
    clean_base_url = base_url.rstrip('/').replace('/v1', '')
    model = LlamaCppModel(
        base_url=clean_base_url,
        params={**params, "max_tokens": 100}
    )
    
    agent = Agent(model=model)
    
    start_time = time.time()
    response = agent(prompt)
    elapsed = time.time() - start_time
    
    # Extract text from response
    if hasattr(response, 'message') and 'content' in response.message:
        text_content = ""
        for content_block in response.message['content']:
            if 'text' in content_block:
                text_content += content_block['text']
        response_text = text_content.strip()
    else:
        response_text = str(response)
    
    # Truncate long responses for display
    display_response = response_text[:200] + "..." if len(response_text) > 200 else response_text
    print(f"Response: {display_response}")
    print(f"\nTime: {elapsed:.2f}s")
    print("=" * 60)
    
    return response_text, elapsed


def get_sampling_strategies() -> List[Dict[str, Any]]:
    """
    Get a collection of predefined sampling strategies for testing.
    
    Returns:
        List of dictionaries containing strategy configurations
    """
    return [
        {
            "name": "Conservative (low temp, high quality)",
            "params": {
                "temperature": 0.3,
                "top_k": 10,
                "repeat_penalty": 1.2
            }
        },
        {
            "name": "Mirostat 2 (perplexity control)",
            "params": {
                "temperature": 0.7,
                "mirostat": 2,
                "mirostat_lr": 0.1,
                "mirostat_ent": 5.0
            }
        },
        {
            "name": "Top-k + Min-p (quality filtering)",
            "params": {
                "temperature": 0.7,
                "top_k": 40,
                "min_p": 0.05
            }
        },
        {
            "name": "TFS + Typical (tail-free sampling)",
            "params": {
                "temperature": 0.7,
                "tfs_z": 0.95,
                "typical_p": 0.95
            }
        },
        {
            "name": "Creative (high temperature)",
            "params": {
                "temperature": 1.0,
                "top_k": 50,
                "top_p": 0.9
            }
        }
    ]


def test_structured_output(output_model: Type[BaseModel], prompt: str,
                          base_url: str = "http://localhost:8080",
                          temperature: float = 0.5,
                          max_tokens: int = 300) -> BaseModel:
    """
    Test structured output generation with a Pydantic model.
    
    Args:
        output_model: Pydantic model class defining the expected structure
        prompt: Input prompt for generation
        base_url: Base URL for the LlamaCpp server
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
    
    Returns:
        Instance of the output_model with generated data
    """
    # Ensure base_url doesn't have /v1 suffix to avoid double /v1 in URL
    clean_base_url = base_url.rstrip('/').replace('/v1', '')
    model = LlamaCppModel(
        base_url=clean_base_url,
        params={
            "temperature": temperature,
            "max_tokens": max_tokens
        }
    )
    
    agent = Agent(model=model)
    
    # Generate structured output
    result = agent.structured_output(output_model, prompt)
    return result


def run_grammar_constraints_demo(base_url: str = "http://localhost:8080") -> None:
    """
    Run a comprehensive demonstration of grammar constraints.
    
    Args:
        base_url: Base URL for the LlamaCpp server
    """
    print("Grammar Constraints Demonstration")
    print("=" * 80)
    
    grammars = get_predefined_grammars()
    
    for grammar_name, config in grammars.items():
        try:
            demonstrate_grammar_constraint(
                grammar=config["grammar"],
                prompt=config["example_prompt"],
                description=config["description"],
                base_url=base_url
            )
        except Exception as e:
            print(f"Error testing {grammar_name}: {e}")
            print("=" * 60)
        
        print()  # Add spacing between tests


def run_sampling_strategies_demo(prompt: str = "Write a creative story opening about a mysterious door:",
                               base_url: str = "http://localhost:8080") -> List[Dict[str, Any]]:
    """
    Run a comprehensive demonstration of sampling strategies.
    
    Args:
        prompt: Prompt to use for testing all strategies
        base_url: Base URL for the LlamaCpp server
    
    Returns:
        List of results with response and timing information
    """
    print("🎲 Sampling Strategies Demonstration")
    print("=" * 80)
    print(f"Test prompt: {prompt}")
    print("=" * 80)
    
    strategies = get_sampling_strategies()
    results = []
    
    for strategy in strategies:
        try:
            response, elapsed = test_sampling_strategy(
                strategy["params"], 
                strategy["name"], 
                prompt,
                base_url=base_url
            )
            results.append({
                "name": strategy["name"],
                "response": response,
                "time": elapsed,
                "params": strategy["params"]
            })
        except Exception as e:
            print(f"Error testing {strategy['name']}: {e}")
            print("=" * 60)
    
    return results


def create_json_grammar(schema: Dict[str, Any]) -> str:
    """
    Create a GBNF grammar from a JSON schema (simplified implementation).
    
    Args:
        schema: JSON schema dictionary
    
    Returns:
        GBNF grammar string
    
    Note:
        This is a simplified implementation. For production use,
        consider using llama.cpp's built-in JSON schema support.
    """
    # This is a basic implementation for common cases
    if schema.get("type") == "object":
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        # Build simple object grammar
        pairs = []
        for prop_name, prop_schema in properties.items():
            if prop_schema.get("type") == "string":
                pairs.append(f'"\"{prop_name}\"" ws ":" ws string')
            elif prop_schema.get("type") == "integer":
                pairs.append(f'"\"{prop_name}\"" ws ":" ws number')
            elif prop_schema.get("type") == "boolean":
                pairs.append(f'"\"{prop_name}\"" ws ":" ws boolean')
        
        if pairs:
            pairs_rule = " ws \",\" ws ".join(pairs)
            return f'''root ::= "{{" ws {pairs_rule} ws "}}"
string ::= "\\"" [^"]* "\\""
number ::= "-"? [0-9]+
boolean ::= "true" | "false" 
ws ::= [ \\t\\n]*'''
    
    # Fallback to generic JSON grammar
    return '''root ::= object
object ::= "{" pair ("," pair)* "}"
pair ::= string ":" value
string ::= "\\"" [^"]* "\\""
value ::= string | number | boolean | "null" | array | object
array ::= "[" (value ("," value)*)? "]"
number ::= "-"? [0-9]+ ("." [0-9]+)?
boolean ::= "true" | "false"
ws ::= [ \\t\\n]*'''