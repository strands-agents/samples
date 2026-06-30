# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

nova_premier = [
    {
        "bedrock_region": "us-west-2",  # Oregon
        "model_type": "nova",
        "model_id": "us.amazon.nova-premier-v1:0",
    },
    {
        "bedrock_region": "us-east-1",  # N.Virginia
        "model_type": "nova",
        "model_id": "us.amazon.nova-premier-v1:0",
    },
    {
        "bedrock_region": "us-east-2",  # Ohio
        "model_type": "nova",
        "model_id": "us.amazon.nova-premier-v1:0",
    },
]

nova_pro_models = [  # Nova Pro
    {
        "bedrock_region": "us-west-2",  # Oregon
        "model_type": "nova",
        "model_id": "us.amazon.nova-pro-v1:0",
    },
    {
        "bedrock_region": "us-east-1",  # N.Virginia
        "model_type": "nova",
        "model_id": "us.amazon.nova-pro-v1:0",
    },
    {
        "bedrock_region": "us-east-2",  # Ohio
        "model_type": "nova",
        "model_id": "us.amazon.nova-pro-v1:0",
    },
]

nova_lite_models = [  # Nova Lite
    {
        "bedrock_region": "us-west-2",  # Oregon
        "model_type": "nova",
        "model_id": "us.amazon.nova-lite-v1:0",
    },
    {
        "bedrock_region": "us-east-1",  # N.Virginia
        "model_type": "nova",
        "model_id": "us.amazon.nova-lite-v1:0",
    },
    {
        "bedrock_region": "us-east-2",  # Ohio
        "model_type": "nova",
        "model_id": "us.amazon.nova-lite-v1:0",
    },
]

nova_micro_models = [  # Nova Micro
    {
        "bedrock_region": "us-west-2",  # Oregon
        "model_type": "nova",
        "model_id": "us.amazon.nova-micro-v1:0",
    },
    {
        "bedrock_region": "us-east-1",  # N.Virginia
        "model_type": "nova",
        "model_id": "us.amazon.nova-micro-v1:0",
    },
    {
        "bedrock_region": "us-east-2",  # Ohio
        "model_type": "nova",
        "model_id": "us.amazon.nova-micro-v1:0",
    },
]

claude_sonnet_4_6_models = [  # Sonnet 4.6
    {
        "bedrock_region": "us-west-2",  # Oregon
        "model_type": "claude",
        "model_id": "us.anthropic.claude-sonnet-4-6",
    },
    {
        "bedrock_region": "us-east-1",  # N.Virginia
        "model_type": "claude",
        "model_id": "us.anthropic.claude-sonnet-4-6",
    },
    {
        "bedrock_region": "us-east-2",  # Ohio
        "model_type": "claude",
        "model_id": "us.anthropic.claude-sonnet-4-6",
    },
]

claude_sonnet_4_6_alt_models = [  # Sonnet 4.6 (alt slot)
    {
        "bedrock_region": "us-west-2",  # Oregon
        "model_type": "claude",
        "model_id": "us.anthropic.claude-sonnet-4-6",
    },
    {
        "bedrock_region": "us-east-1",  # N.Virginia
        "model_type": "claude",
        "model_id": "us.anthropic.claude-sonnet-4-6",
    },
    {
        "bedrock_region": "us-east-2",  # Ohio
        "model_type": "claude",
        "model_id": "us.anthropic.claude-sonnet-4-6",
    },
]

claude_haiku_4_5_models = [  # Haiku 4.5
    {
        "bedrock_region": "us-west-2",  # Oregon
        "model_type": "claude",
        "model_id": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    },
    {
        "bedrock_region": "us-east-1",  # N.Virginia
        "model_type": "claude",
        "model_id": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    },
    {
        "bedrock_region": "us-east-2",  # Ohio
        "model_type": "claude",
        "model_id": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    },
]

claude_4_sonnet_models = [  # Claude 4 Sonnet
    {
        "bedrock_region": "us-west-2",  # Oregon
        "model_type": "claude",
        "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
    },
    {
        "bedrock_region": "us-east-1",  # N.Virginia
        "model_type": "claude",
        "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
    },
    {
        "bedrock_region": "us-east-2",  # Ohio
        "model_type": "claude",
        "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
    },
]

claude_4_5_sonnet_models = [  # Claude 4.5 Sonnet
    {
        "bedrock_region": "us-west-2",  # Oregon
        "model_type": "claude",
        "model_id": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    },
    {
        "bedrock_region": "us-east-1",  # N.Virginia
        "model_type": "claude",
        "model_id": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    },
    {
        "bedrock_region": "us-east-2",  # Ohio
        "model_type": "claude",
        "model_id": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    },
]

def get_model_info(model_name):
    """
    Get model information based on model name.

    Args:
        model_name (str): Name of the model

    Returns:
        list: List of model configurations
    """
    models = []

    if model_name == "Nova Pro":
        models = nova_pro_models
    elif model_name == "Nova Lite":
        models = nova_lite_models
    elif model_name == "Nova Micro":
        models = nova_micro_models
    elif model_name == "Claude 4 Sonnet":
        models = claude_4_sonnet_models
    elif model_name == "Claude Sonnet 4.6":
        models = claude_sonnet_4_6_models
    elif model_name == "Nova Premier":
        models = nova_premier
    elif model_name == "Claude 4.5 Sonnet":
        models = claude_4_5_sonnet_models
    return models


STOP_SEQUENCE_CLAUDE = "\n\nHuman:"
STOP_SEQUENCE_NOVA = '"\n\n<thinking>", "\n<thinking>", " <thinking>"'


def get_stop_sequence(model_name):
    """
    Get stop sequence based on model name.

    Args:
        model_name (str): Name of the model

    Returns:
        str: Stop sequence for the model
    """
    models = get_model_info(model_name)

    model_type = models[0]["model_type"]

    if model_type == "claude":
        return STOP_SEQUENCE_CLAUDE
    elif model_type == "nova":
        return STOP_SEQUENCE_NOVA
    else:
        return ""
