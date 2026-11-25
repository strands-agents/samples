"""Pick the model the agent uses, based on environment variables.

MODEL_PROVIDER=bedrock (default) uses Amazon Bedrock, MODEL_PROVIDER=openai
uses OpenAI. See .env.example for the settings each provider reads.
"""

import os

from dotenv import load_dotenv
from strands.models import Model


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Set {name} in your environment or .env file.")
    return value


def _has_aws_credentials() -> bool:
    import boto3

    return boto3.Session().get_credentials() is not None


def build_model() -> Model:
    """Return a Bedrock or OpenAI model, depending on MODEL_PROVIDER."""
    load_dotenv()
    provider = os.getenv("MODEL_PROVIDER", "bedrock").strip().lower()

    if provider == "bedrock":
        from strands.models.bedrock import BedrockModel

        if not _has_aws_credentials():
            raise SystemExit(
                "No AWS credentials found. Configure them (for example with "
                "`aws configure`), or set MODEL_PROVIDER=openai."
            )
        return BedrockModel(
            model_id=os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-pro-v1:0"),
            region_name=os.getenv("AWS_REGION") or "us-east-1",
        )

    if provider == "openai":
        from strands.models.openai import OpenAIModel

        return OpenAIModel(
            client_args={"api_key": _require("OPENAI_API_KEY")},
            model_id=os.getenv("OPENAI_MODEL_ID", "gpt-4o-mini"),
        )

    raise SystemExit(
        f"MODEL_PROVIDER must be 'bedrock' or 'openai', not '{provider}'."
    )
