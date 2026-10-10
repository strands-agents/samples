"""
Script to generate ground truth data for various domains.
Converts instructions into natural language questions and generates tool outputs.
"""

# Libraries
import sys
import os
import json
import argparse
from bs4 import BeautifulSoup
import warnings
import time
import boto3
from botocore.config import Config
from typing import Dict, Type, List
import importlib

# Append necessary paths
sys.path.append('../data/ma-bench/')
sys.path.append('../data/tau-bench/')


def setup_bedrock_client(region_name="us-east-1"):
    """
    Set up and return a boto3 bedrock-runtime client with retry configuration.
    
    Args:
        region_name (str): AWS region name
        
    Returns:
        boto3.client: Configured bedrock-runtime client
    """
    my_config = Config(
        region_name=region_name,
        signature_version='v4',
        retries={
            'max_attempts': 3,
            'mode': 'standard'
        }
    )
    
    return boto3.client(
        service_name="bedrock-runtime",
        config=my_config,
    )


def generate_question(instruction, bedrock_runtime):
    """
    Generate a natural language question from an instruction using Claude model.
    
    Args:
        instruction (str): The instruction to convert to a question
        bedrock_runtime: boto3 bedrock-runtime client
        
    Returns:
        str: Generated question
    """
    # Select the model to use
    user_bedrock_model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    # Remove specific text if found
    find = "You are reactive to the agent and will not say anything that is not asked. "
    if find in instruction:
        instruction = instruction.replace(find, "")
    
    # Set up the prompt template
    user_prompt_template = """
    You are an instruction rewritter. 
    Your task is to rewrite the instruction by following a set of rules.
    Below is the instruction for you in <instruction></instruction> XML tags.
    Below is the set of rules for you in <rules></rules> XML tags.
    Output the newly generated instruction in the <question></question> XML tags.

    <instruction>
    {instruction}
    </instruction>

    <rules>
    1. Change the instruction to the first-person voice.
    2. Keep the used id (for example sofia_kim_7287 as it is in the generated question)
    3. Include your name and zip code if provided. 
    4. Remove the description of person's characteristics. 
    5. The new instruction should be easy to understand and the customer representative should be able to help without asking follow up questions.
    6. Do not hallucinate information about zip code that is not provided in the instruction.
    7. For example, if the agent asks for the order id but it is not mentioned in the instruction, do not make up an order id, just say you do not remember or have it.
    </rules>
    """
    
    # Fill in the instruction
    prompt = user_prompt_template.replace("{instruction}", instruction)
    
    # Set up the model parameters
    model_kwargs = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "temperature": 0.0,
        "top_k": 250,
        "top_p": 1,
        "stop_sequences": ["Human"],
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    }
    
    body = json.dumps(model_kwargs)
    accept = "application/json"
    contentType = "application/json"

    # Call the model
    response = bedrock_runtime.invoke_model(
        body=body,
        modelId=user_bedrock_model_id,
        accept=accept,
        contentType=contentType
    )

    # Process the response
    response_body = json.loads(response.get("body").read())
    question_text = response_body['content'][0]['text']
    soup = BeautifulSoup(question_text, 'html.parser')
    question = soup.find('question').string
    
    return question


def generate_tooloutput(actions, tools_map, data):
    """
    Generate results for a sequence of tool actions.
    
    Args:
        actions (List[dict]): List of actions with name and arguments
        tools_map (Dict[str, Tool]): Mapping of tool names to tool objects
        data: Data to pass to tools
        
    Returns:
        List: Results of tool actions
    """
    action_results = []
    for action in actions:
        result = tools_map[action["name"]].invoke(data, **action["arguments"])
        action_results.append(result)
    return action_results


def load_domain_modules(domain):
    """
    Load domain-specific modules.
    
    Args:
        domain (str): Domain name (e.g., 'airline', 'retail')
        
    Returns:
        tuple: (ALL_TOOLS, load_data, tasks, WIKI)
    """
    try:
        tools_module = importlib.import_module(f"tau_bench.envs.{domain}.tools")
        ALL_TOOLS = tools_module.ALL_TOOLS
        
        data_module = importlib.import_module(f"tau_bench.envs.{domain}.data")
        load_data = data_module.load_data
        
        tasks_module = importlib.import_module(f"tau_bench.envs.{domain}.tasks")
        tasks = tasks_module.tasks
        
        wiki_module = importlib.import_module(f"tau_bench.envs.{domain}.wiki")
        WIKI = wiki_module.WIKI
        
        return ALL_TOOLS, load_data, tasks, WIKI
    except ImportError as e:
        print(f"Error importing modules for domain '{domain}': {e}")
        sys.exit(1)


def refresh_setting(domain):
    """
    Refresh the data and tools mapping for a specific domain.
    
    Args:
        domain (str): Domain name
        
    Returns:
        tuple: (data, tools_map)
    """
    ALL_TOOLS, load_data, _, _ = load_domain_modules(domain)
    data = load_data()
    tools_map: Dict[str, Type[Tool]] = {
        tool.get_info()["function"]["name"]: tool for tool in ALL_TOOLS
    }
    return data, tools_map


def process_tasks(domain, task_indices=None, delay=15):
    """
    Process the tasks by generating questions and tool outputs.
    
    Args:
        domain (str): Domain name
        task_indices (List[int], optional): Indices of tasks to process. 
                                           If None, process all except specific indices.
        delay (int): Delay in seconds between API calls
        
    Returns:
        List[dict]: Updated tasks with questions and action results
    """
    # Initialize the bedrock client
    bedrock_runtime = setup_bedrock_client()
    
    # Load domain-specific modules
    _, _, tasks, _ = load_domain_modules(domain)
    
    # Define indices to skip if task_indices is None
    # Note: These indices are specific to the airline domain
    skip_indices = [5, 9, 24, 27, 28, 36, 38, 40, 41, 42, 44, 46] if domain == "airline" else []
    
    for i, task in enumerate(tasks):
        # Skip if task index is in skip_indices and we're processing all tasks
        if task_indices is None and i in skip_indices:
            continue
            
        # Skip if we're only processing specific tasks and this isn't one of them
        if task_indices is not None and i not in task_indices:
            continue
            
        print(f"Processing task {i}")
        data, tools_map = refresh_setting(domain)

        user_id = task["user_id"]
        actions = task["actions"]
        instruction = task["instruction"]

        # Generate the question
        question = generate_question(instruction, bedrock_runtime)
        task["question"] = question

        # Generate tool outputs
        action_results = generate_tooloutput(actions, tools_map, data)
        
        # Try to parse JSON results
        try:
            task["action_results"] = [json.loads(action_result) for action_result in action_results]
        except:
            task["action_results"] = action_results

        # Sleep to avoid rate limiting
        time.sleep(delay)
    
    return tasks


def save_tasks(tasks, domain):
    """
    Save tasks to a JSON file.
    
    Args:
        tasks (List[dict]): Tasks to save
        domain (str): Domain name for the path
        
    Returns:
        str: Path to the saved file
    """
    output_path = os.path.join("..", "data", "tau-bench", "tau_bench", "envs", domain, "tasks_singleturn.json")
    
    with open(output_path, "w") as file:
        json.dump(tasks, file)
        
    return output_path


def main():
    """
    Main function to run the script.
    """
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate ground truth data for specified domain")
    parser.add_argument("--domain", type=str, required=True, help="Domain name (e.g., 'airline', 'retail')")
    parser.add_argument("--task-indices", type=int, nargs="+", help="Specific task indices to process")
    
    args = parser.parse_args()
    
    # Set the warning filter
    warnings.filterwarnings("ignore")
    
    # Process tasks for the specified domain
    updated_tasks = process_tasks(args.domain, args.task_indices)
    
    # Save the updated tasks
    output_path = save_tasks(updated_tasks, args.domain)
    print(f"Tasks saved to {output_path}")


if __name__ == "__main__":
    main()
