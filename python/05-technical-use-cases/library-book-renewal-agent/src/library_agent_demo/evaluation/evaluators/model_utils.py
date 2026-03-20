"""Model utilities for evaluators."""

from aws_bedrock_token_generator import provide_token
from strands.models.openai import OpenAIModel


def create_judge_model(model_id: str = "moonshotai.kimi-k2.5", region: str = "us-west-2") -> OpenAIModel:
    """Create an OpenAI model using Bedrock Mantle endpoint."""
    api_key = provide_token(region=region)
    return OpenAIModel(
        client_args={
            "api_key": api_key,
            "base_url": f"https://bedrock-mantle.{region}.api.aws/v1",
        },
        model_id=model_id,
    )
