'''
MIT No Attribution

Copyright 2024 Amazon Web Services

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

'''
import os
import json
from typing import Dict, Any
import boto3
import sys
from botocore.exceptions import ClientError
from io import StringIO
import base64

from strands import Agent, tool
from strands.models import BedrockModel


from tools.util import get_current_time
from tools.site_info import  get_site_info, get_timeseries_data



BUCKET_NAME = os.environ.get("AGENT_BUCKET")
REGION = os.environ['AWS_REGION']
WS_API_ENDPOINT = os.environ['WS_API_ENDPOINT']
#replace the wss: to https: and append /$default to WS_API_ENDPOINT
WS_REPLY_API_ENDPOINT = WS_API_ENDPOINT.replace("wss:", "https:") + "/$default"

#create S3 client
s3_client = boto3.client('s3')
# Create API Gateway management client
api_client = boto3.client('apigatewaymanagementapi',
                        endpoint_url= WS_REPLY_API_ENDPOINT, 
                        region_name = REGION)

#Model id for the FM in Bedrock. Select a model that supports tools
MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
#System prompt for the agent. Explain here what you want the agent to be.
SYSTEM_PROMPT = """  
               You are a smart data analytics assistant. You role is to follow the below steps to answer the questions asked by the human data analyst.
                1. If the response requires ANY site information or timeseries data, ALWAYS generate the python code to generate the answer and call the execute_code tool. You HAVE to do this 
                    since the response from these functions can be very large. The return format of these tools are strictly defined as shown in the tool documentation.
                    eg: if the user asks about a zones in a particular floor for the building, write and execute the code get a list of assets of type 'Floor', get the id of that floor and then 
                        write code and execute to list the number of children for that floor id of type zone. These types are fixed and allowed values are listed in get_site_info documentation
                2. If the response requires ANY mathematical calculations (eg:count, average, min, max), ALWAYS generate the python code to generate the answer and call the execute_code tool. 
                    DO NOT do ANY mathematical calculations without generating code. 
                    The code executed inside the execute_code tool call call the get_site_info, get_timeseries_data and get_current_time tools. 
                    CALL these functions to retrieve the data for processing. eg: get_site_info('s123'). Otherwise the code execution DOES NOT have access to your tool_result.
                    ALWAYS use the print statement at the end to return the end result. eg: instead of sum, use print(sum) at the end of the generated code.
                3. Use the resulting answer to give the response to user
            """

@tool
def execute_code(code: str) -> Dict[str, str]:
    """
    Executes the provided Python code in a controlled environment and captures its output.

    This function executes the given code with access to specific predefined functions
    while capturing both standard output and standard error streams. The code is also
    saved to a file for reference.

    Args:
        code (str): The Python code to be executed as a string.

    Returns:
        dict: A dictionary containing two keys:
            - 'stdout' (str): The captured standard output from the code execution
            - 'stderr' (str): The captured standard error output from the code execution

    Available Functions:
        The below functions are available in the code which are the SAME as your tool definitions

        - get_site_info: Retrieves site information
        - get_timeseries_data: Retrieves time series data
        - get_current_time: Gets the current time
 

    Example:
        >>> result = execute_code('print("Hello World")')
        >>> print(result)
        {'stdout': 'Hello World\n', 'stderr': ''}

    Note:
        - The code is executed in a restricted environment with only specific functions available
        - All stdout is captured and returned rather than being printed directly
    """
    
    stdout_buffer = StringIO()
    stderr_buffer = StringIO()
    
    # Save the originals
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    # Redirect stdout to our buffer
    sys.stdout = stdout_buffer
    sys.stderr = stderr_buffer

    available_functions = {
        'get_site_info': get_site_info,
        'get_timeseries_data': get_timeseries_data,
        'get_current_time': get_current_time
    }

    #execute the code snippet
    exec(code, available_functions)

    # Restore the original stdout
    sys.stdout = original_stdout
    sys.stderr = original_stderr

    # Get the captured output
    output = stdout_buffer.getvalue()
    err = stderr_buffer.getvalue()
    return {
            "stdout" : output , 
            "stderr" : err
            }


def get_agent_object(key: str):

    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
        content = response['Body'].read().decode('utf-8')
        state = json.loads(content)
        
        return create_agent(state['messages'])
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return create_agent([])
        else:
            raise  # Re-raise if it's a different error

def put_agent_object(key: str, agent: Agent):
    
    state = {
        "messages": agent.messages,
        "system_prompt": agent.system_prompt
    }
    
    content = json.dumps(state)
    
    response = s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=content.encode('utf-8'),
        ContentType='application/json'
    )
    
    return response

def create_agent(messages):

    model = BedrockModel(
        model_id= MODEL_ID,
        max_tokens=4096,
        
    )

    return Agent(
        model = model,
        system_prompt = SYSTEM_PROMPT,
        messages = messages,
        tools = [ 
                    get_current_time,
                    execute_code,
                    get_site_info,
                    get_timeseries_data
                ]
    )

#send a reply back to the client specified by the connection_id
def send_to_websocket_client(last_message, connection_id):
 
    try:
        #replace new lines with <br>
        last_message = last_message.replace("\n", "<br>")

        # Send message to connected client
        api_client.post_to_connection(
            Data=last_message,
            ConnectionId=connection_id
        )
    except Exception as e:
        print(f"Error sending message to websocket client: {str(e)}")   

def lambda_handler(event: Dict[str, Any], _context) -> str:

    print(event)
    #clear the id token if lingering from previous invocation
    os.environ['ID_TOKEN'] = ""
    # get connection id for sending reply back to websocket client
    connection_id = event['connection_id']
    # set the id token in env var
    os.environ['ID_TOKEN'] = event['id_token']

    #Langfuse tracing setup
    langfuse_pk = os.environ.get("LANGFUSE_PK")
    langfuse_sk = os.environ.get("LANGFUSE_SK")
    # Set up endpoint
    otel_endpoint = str(os.environ.get("LANGFUSE_HOST", "")) + "/api/public/otel/v1/traces"
    # Create authentication token:
    auth_token = base64.b64encode(f"{langfuse_pk}:{langfuse_sk}".encode()).decode()
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = otel_endpoint
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {auth_token}"

    payload = {}
    if 'body' in event:
        payload = event['body']

    if 'human_message' in payload:
        human_message = payload['human_message']
        thread_id = payload['thread_id']

        try:

            agent = get_agent_object(key=f"threads/{thread_id}.json")            
            response = agent(human_message)
            content = str(response)
            put_agent_object(key=f"threads/{thread_id}.json", agent=agent)        
            send_to_websocket_client(content, connection_id)

        except Exception as e:
            print(e)
