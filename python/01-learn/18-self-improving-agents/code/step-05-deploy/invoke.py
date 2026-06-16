"""Invoke a deployed AgentCore agent from anywhere.

Usage:
    export AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:...:runtime/aim308_research_agent-XYZ
    python invoke.py "what can you do?"
"""
import json
import os
import sys

import boto3
from botocore.config import Config

REGION = os.environ.get("AWS_REGION", "us-east-1")
ARN = os.environ.get("AGENT_ARN")


def main():
    if not ARN:
        print("⚠️  set AGENT_ARN (printed by `agentcore deploy`)")
        sys.exit(1)

    prompt = " ".join(sys.argv[1:]) or "Hello - introduce yourself."
    session_id = os.environ.get("AIM308_SESSION", "nyc-summit-demo")

    cfg = Config(read_timeout=900, connect_timeout=60)
    client = boto3.client("bedrock-agentcore", region_name=REGION, config=cfg)

    resp = client.invoke_agent_runtime(
        agentRuntimeArn=ARN,
        qualifier="DEFAULT",
        runtimeSessionId=session_id,
        payload=json.dumps({"prompt": prompt, "mode": "sync"}),
    )

    out = b""
    for chunk in resp.get("response", []):
        if isinstance(chunk, bytes):
            out += chunk
        elif isinstance(chunk, str):
            out += chunk.encode()
    print(out.decode("utf-8", errors="ignore"))


if __name__ == "__main__":
    main()
