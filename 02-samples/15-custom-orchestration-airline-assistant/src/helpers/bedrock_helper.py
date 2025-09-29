# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import json
import base64
import boto3
import pathlib
from botocore.config import Config
from botocore.exceptions import ClientError

#from mistral_common.protocol.instruct.messages import (
#    UserMessage,
#)
#from mistral_common.protocol.instruct.request import ChatCompletionRequest
#from mistral_common.tokens.tokenizers.mistral import MistralTokenizer


# Sonnet 3.5 default quota only available in us-west-2
BEDROCK_CONFIG = Config(
    region_name = 'us-west-2',
    signature_version = 'v4',
    read_timeout = 500,
    retries = {
        'max_attempts': 3,
        'mode': 'standard'
    }
)


BEDROCK_RT = boto3.client("bedrock-runtime", config = BEDROCK_CONFIG)

BEDROCK_EAST_CONFIG = Config(
    region_name = 'us-east-1',
    signature_version = 'v4',
    read_timeout = 500,
    retries = {
        'max_attempts': 3,
        'mode': 'standard'
    }
)

BEDROCK_RT_EAST = boto3.client("bedrock-runtime", config = BEDROCK_EAST_CONFIG)

HAIKU_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
SONNET35_MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"
SONNET_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"
OPUS_MODEL_ID = "anthropic.claude-3-opus-20240229-v1:0"

LLAMA3_8B_MODEL_ID = "meta.llama3-8b-instruct-v1:0"
LLAMA3_70B_MODEL_ID = "meta.llama3-70b-instruct-v1:0"

LLAMA31_8B_MODEL_ID = "meta.llama3-1-8b-instruct-v1:0"
LLAMA31_70B_MODEL_ID = "meta.llama3-1-70b-instruct-v1:0"

LLAMA32_1B_MODEL_ID = "us.meta.llama3-2-1b-instruct-v1:0"
LLAMA32_3B_MODEL_ID = "us.meta.llama3-2-3b-instruct-v1:0"
LLAMA32_11B_MODEL_ID = "us.meta.llama3-2-11b-instruct-v1:0"
LLAMA32_90B_MODEL_ID = "us.meta.llama3-2-90b-instruct-v1:0"

MISTRAL_L_MODEL_ID = "mistral.mistral-large-2402-v1:0"
MISTRAL_S_MODEL_ID = "mistral.mistral-small-2402-v1:0"
MISTRAL_L2_MODEL_ID = "mistral.mistral-large-2407-v1:0"

NOVA_PRO_MODEL_ID = "us.amazon.nova-pro-v1:0"
NOVA_LITE_MODEL_ID = "us.amazon.nova-lite-v1:0"
NOVA_MICRO_MODEL_ID = "us.amazon.nova-micro-v1:0"
NOVA_PREMIER_MODEL_ID ="us.amazon.nova-premier-v1:0"


CLAUDE_ID_LIST = [ HAIKU_MODEL_ID, 
                  SONNET35_MODEL_ID,
                  SONNET_MODEL_ID,
                  OPUS_MODEL_ID ]

LLAMA_ID_LIST = [LLAMA3_8B_MODEL_ID, 
                 LLAMA3_70B_MODEL_ID, 
                 LLAMA31_8B_MODEL_ID, 
                 LLAMA31_70B_MODEL_ID,
                 LLAMA32_1B_MODEL_ID,
                 LLAMA32_3B_MODEL_ID,
                 LLAMA32_11B_MODEL_ID,
                 LLAMA32_90B_MODEL_ID ]

MISTRAL_LIST = [MISTRAL_L_MODEL_ID, 
                MISTRAL_S_MODEL_ID ]

MISTRAL_V2_LIST = [MISTRAL_L2_MODEL_ID]

MISTRAL_ALL_LIST = MISTRAL_LIST + MISTRAL_V2_LIST

NOVA_LIST = [ NOVA_PRO_MODEL_ID, 
             NOVA_LITE_MODEL_ID, 
             NOVA_MICRO_MODEL_ID,
            NOVA_PREMIER_MODEL_ID]

def get_bedrock_response( user_message="Hello!",
                         system = "",
                         assistant_message= "",
                         max_tokens=250, 
                         temp=0,
                         topK=50, 
                         stop_sequences=["Human:"], 
                         model_id = SONNET35_MODEL_ID, 
                         text_only=True):
    '''
    Bedrock helper function to invoke Bedrock call
    '''
    if model_id in CLAUDE_ID_LIST:
        response = get_claude_response(user_message=user_message,
                                       system = system,
                                       assistant_message= assistant_message,
                                       max_tokens=max_tokens, 
                                       temp=temp,
                                       topK=topK, 
                                       stop_sequences=stop_sequences, 
                                       model_id = model_id)
    elif model_id in LLAMA_ID_LIST:
        response = get_llama3_response( user_message = user_message,
                                      system_message = system,
                                      assistant_message = assistant_message,
                                      max_tokens=max_tokens, 
                                      temp=temp,
                                      stop_sequences=stop_sequences, 
                                      model_id = model_id)
    elif model_id in MISTRAL_LIST:
        response = get_mistral_response( user_message = user_message,
                                        system_message = system,
                                        assistant_message = assistant_message,
                                        max_tokens=max_tokens, 
                                        temp=temp,
                                        model_id = model_id)
    elif model_id in MISTRAL_V2_LIST:
        response = get_mistral_v2_response( user_message=user_message,
                                           system = system,
                                           assistant_message= assistant_message,
                                           max_tokens=max_tokens, 
                                           temp=temp,
                                           topK=topK, 
                                           stop_sequences=stop_sequences, 
                                           model_id = model_id )
    elif model_id in NOVA_LIST:
        response = get_nova_response( user_message=user_message,
                                           system = system,
                                           assistant_message= assistant_message,
                                           max_tokens=max_tokens, 
                                           temp=temp,
                                           topK=topK, 
                                           stop_sequences=stop_sequences, 
                                           model_id = model_id )
    else:
        return "Unknown Bedrock Model ID"

    if text_only:
        response = get_bedrock_text_only_response( response, model_id=model_id )

    return response

def get_bedrock_text_only_response( response, model_id=SONNET35_MODEL_ID):
    '''
    Simple function to get the text only response from the raw Bedrock response
    '''

    if model_id in CLAUDE_ID_LIST:
        response = get_claude_response_text( response )
    elif model_id in LLAMA_ID_LIST:
        response = get_llama_response_text( response )
    elif model_id in MISTRAL_LIST:
        response = get_mistral_response_text( response )
    elif model_id in MISTRAL_V2_LIST:
        response = get_mistral_v2_response_text( response )
    elif model_id in NOVA_LIST:
        response = get_nova_response_text( response )

    return response 


############################
#          CLAUDE          #
############################

def create_claude_body( messages = [{"role": "user", "content": "Hello!"}], 
                       system = "You are an AI chatbot.",
                       max_tokens=2048, 
                       temp=0, 
                       topK=250, 
                       stop_sequences=["Human"]):
    """
    Simple function for creating a body for Anthropic Claude models for the Messages API.
    https://docs.anthropic.com/claude/reference/messages_post
    """
    body = {
        "messages": messages,
        "max_tokens": max_tokens,
        "system":system,
        "temperature": temp,
        "anthropic_version":"",
        "top_k": topK,
        "stop_sequences": stop_sequences
    }
    
    return body

def get_claude_response(user_message="Hello!", 
                        system = "You are an AI chatbot.",
                        assistant_message= "",
                        max_tokens=250, 
                        temp=0,
                        topK=250, 
                        stop_sequences=["Human:"], 
                        model_id = SONNET35_MODEL_ID):
    """
    Simple function for calling Claude via boto3 and the invoke_model API. 
    """
    
    if assistant_message == "":
        messages = [{"role": "user", "content": user_message}]
    else:
        messages = [{"role": "user", "content": user_message}, {"role": "assistant", "content": assistant_message}]
    
    body = create_claude_body(messages=messages, 
                              system = system,
                              max_tokens=max_tokens, 
                              temp=temp,
                              topK=topK, 
                              stop_sequences=stop_sequences)
    
    response = BEDROCK_RT.invoke_model(modelId=model_id, body=json.dumps(body))
    response = json.loads(response['body'].read().decode('utf-8'))
    
    return response

def get_claude_response_text( response ):
    return response['content'][0]['text']

###########################
#         LLAMA 3         #
###########################

def create_llama3_prompt(user_message = "Hello!",
                         system_message = "You are an AI chatbot.",
                         assistant_message = ""
                        ):
    prompt = f"""
    <|begin_of_text|><|start_header_id|>system<|end_header_id|>{system_message}<|eot_id|>
    <|start_header_id|>user<|end_header_id|>{user_message}<|eot_id|>
    <|start_header_id|>assistant<|end_header_id|>{assistant_message}
    """
    return prompt

def get_llama3_response(user_message = "Hello!",
                        system_message = "You are an AI chatbot.",
                        assistant_message = "",
                        max_tokens=250, 
                        temp=0,
                        stop_sequences=["Human:"], 
                        model_id = LLAMA31_70B_MODEL_ID):
    prompt = create_llama3_prompt(user_message=user_message, system_message=system_message,assistant_message=assistant_message)
    #print(prompt)
    try:
        body = {
            "prompt": prompt,
            "temperature": temp,
            "top_p": 1,
            "max_gen_len": max_tokens,
        }

        response = BEDROCK_RT.invoke_model(
            modelId=model_id, body=json.dumps(body)
        )

        response_body = json.loads(response["body"].read())
        return response_body

    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        raise
        
def get_llama_response_text(response):
    completion = response["generation"]
    return completion