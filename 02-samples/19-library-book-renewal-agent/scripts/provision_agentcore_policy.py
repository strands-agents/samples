#!/usr/bin/env python3
"""
Convenience script to provision AgentCore policy using CDK stack outputs.

This script automatically retrieves the gateway ID from the deployed CDK stack
and provisions the AgentCore policy.
"""

import json
import subprocess
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from library_agent_demo.infrastructure.provision_policy import (
    AgentCorePolicyProvisioner,
)


def get_stack_outputs(stack_name: str) -> dict:
    """Get CDK stack outputs.

    Args:
        stack_name: Name of the CDK stack

    Returns:
        Dictionary of stack outputs
    """
    try:
        # Run CDK list to get stack names
        result = subprocess.run(["cdk", "list"], capture_output=True, text=True, check=True)

        available_stacks = result.stdout.strip().split("\n")
        print(f"Available stacks: {available_stacks}")

        # Find the correct stack name (it might have a suffix)
        actual_stack_name = None
        for stack in available_stacks:
            if stack_name in stack:
                actual_stack_name = stack
                break

        if not actual_stack_name:
            raise ValueError(f"Stack containing '{stack_name}' not found in: {available_stacks}")

        print(f"Using stack: {actual_stack_name}")

        # Get stack outputs
        result = subprocess.run(
            [
                "aws",
                "cloudformation",
                "describe-stacks",
                "--stack-name",
                actual_stack_name,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        stack_data = json.loads(result.stdout)
        outputs = {}

        for output in stack_data["Stacks"][0].get("Outputs", []):
            outputs[output["OutputKey"]] = output["OutputValue"]

        return outputs

    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting stack outputs: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        raise
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise


def main() -> None:
    """Main function."""
    stack_name = "LibraryAgentGatewayStack"
    region = "us-east-1"

    if len(sys.argv) > 1:
        region = sys.argv[1]

    print(f"🚀 Provisioning AgentCore policy for stack: {stack_name}")
    print(f"Region: {region}\n")

    try:
        # Get stack outputs
        print("📋 Getting CDK stack outputs...")
        outputs = get_stack_outputs(stack_name)

        if not outputs:
            print("❌ No stack outputs found")
            sys.exit(1)

        print("Stack outputs:")
        for key, value in outputs.items():
            print(f"  {key}: {value}")

        # Get gateway ID
        gateway_id = outputs.get("GatewayId")
        if not gateway_id:
            print("❌ GatewayId not found in stack outputs")
            print("Available outputs:", list(outputs.keys()))
            sys.exit(1)

        print(f"\n🎯 Found Gateway ID: {gateway_id}")

        # Provision the policy
        print("\n📝 Provisioning AgentCore policy...")
        provisioner = AgentCorePolicyProvisioner(region=region)

        result = provisioner.provision_policy(gateway_id)

        # Verify the attachment
        print("\n🔍 Verifying policy attachment...")
        verification_success = provisioner.verify_policy_attachment(gateway_id)

        if verification_success:
            print("\n✅ AgentCore policy provisioning completed successfully!")
            print(f"Policy ID: {result['policy_id']}")
            print(f"Gateway ID: {result['gateway_id']}")
            print(f"Gateway URL: {outputs.get('GatewayUrl', 'Not available')}")
        else:
            print("\n⚠️  Policy provisioning completed but verification failed")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Policy provisioning failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
