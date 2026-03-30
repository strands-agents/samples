#!/usr/bin/env python3
"""
Simplified setup script for Exa Deep Research Assistant with optional observability.

This script:
1. Helps set up the .env file from .env-obs.example
2. Verifies the Exa API key is configured
3. Creates CloudWatch log group and stream (if using observability)
4. Provides clear instructions for running with or without observability
"""

import os
import sys
import boto3
from pathlib import Path
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Configuration
SERVICE_NAME = "exa-deep-research"
LOG_GROUP = f"agents/{SERVICE_NAME}-logs"
LOG_STREAM = "default"
ENV_FILE = Path(__file__).parent / ".env"
ENV_EXAMPLE = Path(__file__).parent / ".env-obs.example"

def check_env_file():
    """Check if .env file exists."""
    if ENV_FILE.exists():
        print("✅ .env file exists")
        return True
    else:
        print("❌ .env file not found")
        print("   Run ./setup-with-observability.sh first")
        return False

def verify_exa_api_key():
    """Check if Exa API key is configured."""
    load_dotenv(ENV_FILE)
    api_key = os.getenv("EXA_API_KEY", "")

    if not api_key or api_key == "ADD_YOUR_EXA_API_KEY_HERE":
        print("⚠️  Exa API key not configured!")
        print("   Please edit .env and add your Exa API key:")
        print("   EXA_API_KEY=your-key-here")
        print("   Get your key at: https://dashboard.exa.ai/api-keys")
        return False

    print("✅ Exa API key configured")
    return True

def check_observability_enabled():
    """Check if observability is enabled in .env."""
    load_dotenv(ENV_FILE)
    enabled = os.getenv("AGENT_OBSERVABILITY_ENABLED", "true").lower() == "true"

    if enabled:
        print("✅ Observability is ENABLED")
    else:
        print("ℹ️  Observability is DISABLED")
        print("   To enable: Set AGENT_OBSERVABILITY_ENABLED=true in .env")

    return enabled

def create_cloudwatch_resources():
    """Create CloudWatch log group and stream if they don't exist."""
    try:
        # Check AWS credentials
        try:
            boto3.client("sts").get_caller_identity()
        except Exception:
            print("\n⚠️  AWS credentials not configured")
            print("   Run 'aws configure' to set up AWS access")
            print("   Observability will not work without AWS credentials")
            return False

        cloudwatch = boto3.client("logs")

        # Create log group
        try:
            cloudwatch.create_log_group(logGroupName=LOG_GROUP)
            print(f"✅ Created log group: {LOG_GROUP}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
                print(f"✅ Log group already exists: {LOG_GROUP}")
            else:
                print(f"❌ Error creating log group: {e}")
                return False

        # Create log stream
        try:
            cloudwatch.create_log_stream(
                logGroupName=LOG_GROUP,
                logStreamName=LOG_STREAM
            )
            print(f"✅ Created log stream: {LOG_STREAM}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
                print(f"✅ Log stream already exists: {LOG_STREAM}")
            else:
                print(f"❌ Error creating log stream: {e}")
                return False

        return True

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def print_instructions(observability_enabled):
    """Print instructions for running the application."""
    print("\n" + "="*60)
    print("🎉 Setup Complete!")
    print("="*60)

    print("\n📋 How to run the Deep Research Assistant:")

    if observability_enabled:
        print("\n🔍 WITH OBSERVABILITY (traces in CloudWatch):")
        print("   opentelemetry-instrument python deep_research_assistant.py \"your research query\"")
        print("\n   View traces in AWS CloudWatch Console: GenAI Observability Dashboard")
        print(f"   • Service name: {SERVICE_NAME}")

    print("\n🚀 WITHOUT OBSERVABILITY (simple mode):")
    print("   python deep_research_assistant.py \"your research query\"")

    if observability_enabled:
        print("\n💡 To disable observability:")
        print("   Set AGENT_OBSERVABILITY_ENABLED=false in .env")
    else:
        print("\n💡 To enable observability:")
        print("   1. Set AGENT_OBSERVABILITY_ENABLED=true in .env")
        print("   2. Run this setup script again")
        print("   3. Use opentelemetry-instrument when running the app")

    print("\n" + "="*60)

def main():
    """Main setup function."""
    print("🔧 Exa Deep Research Assistant - Observability Setup")
    print("="*60)

    # Step 1: Check .env file exists
    print("\n📁 Step 1: Environment File Check")
    if not check_env_file():
        sys.exit(1)

    # Step 2: Verify Exa API key (warn but don't exit)
    print("\n🔑 Step 2: API Key Verification")
    api_key_configured = verify_exa_api_key()

    # Step 3: Check if observability is enabled
    print("\n📊 Step 3: Observability Configuration")
    observability_enabled = check_observability_enabled()

    # Step 4: Create CloudWatch resources (if observability is enabled)
    if observability_enabled:
        print("\n☁️  Step 4: CloudWatch Setup")
        create_cloudwatch_resources()
    else:
        print("\n☁️  Step 4: CloudWatch Setup - SKIPPED (observability disabled)")

    # Step 5: Print instructions
    print_instructions(observability_enabled)

    # Final warning if API key not configured
    if not api_key_configured:
        print("\n⚠️  REMEMBER: Add your Exa API key to .env before running the application!")

if __name__ == "__main__":
    main()