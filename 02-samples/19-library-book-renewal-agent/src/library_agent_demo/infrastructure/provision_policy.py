"""
AgentCore Policy provisioning script using Boto3.

This script creates and attaches a Cedar policy to the AgentCore Gateway
to enforce the 30-day renewal period constraint.
"""

import sys
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError


class AgentCorePolicyProvisioner:
    """Provisions AgentCore policies using Boto3."""

    def __init__(self, region: str = "us-east-1") -> None:
        """Initialize the policy provisioner.

        Args:
            region: AWS region for the AgentCore service
        """
        self.region = region
        self.control_client = boto3.client("bedrock-agentcore-control", region_name=region)

    def create_renewal_period_policy(self, gateway_arn: str) -> str:
        """Create Cedar policy for 30-day renewal period constraint.

        Args:
            gateway_arn: The ARN of the AgentCore Gateway

        Returns:
            The Cedar policy document as a string
        """
        # Cedar policy to enforce 30-day renewal period constraint
        # Based on the documentation, action format is "TargetName___tool_name"
        # Using a single permit policy with the constraint condition
        cedar_policy = f"""permit(
    principal,
    action == AgentCore::Action::"renewal-server-target___renew_book",
    resource == AgentCore::Gateway::"{gateway_arn}"
) when {{
    context.input.renewal_period <= 30
}};"""

        return cedar_policy.strip()

    def create_or_get_policy_engine(self, name: str = "LibraryRenewalPolicyEngine") -> dict[str, Any]:
        """Create or get existing policy engine.

        Args:
            name: Name for the policy engine

        Returns:
            Dictionary containing policy engine information
        """
        try:
            # Try to find existing policy engine first
            print(f"Checking for existing policy engine: {name}")

            response = self.control_client.list_policy_engines()

            for engine in response.get("policyEngines", []):
                if engine["name"] == name:
                    print(f"✅ Found existing policy engine: {engine['policyEngineId']}")
                    return engine

            # Create new policy engine if not found
            print(f"Creating new policy engine: {name}")

            response = self.control_client.create_policy_engine(
                name=name,
                description="Policy engine for library book renewal constraints",
            )

            policy_engine_id = response["policyEngineId"]
            print(f"✅ Policy engine created: {policy_engine_id}")

            # Wait for policy engine to become active
            print("Waiting for policy engine to become active...")
            self._wait_for_policy_engine_active(policy_engine_id)

            return response

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]

            if error_code == "ConflictException":
                print(f"⚠️  Policy engine with name '{name}' already exists")
                # Try to get it by listing again
                response = self.control_client.list_policy_engines()
                for engine in response.get("policyEngines", []):
                    if engine["name"] == name:
                        return engine
                raise ValueError(f"Policy engine '{name}' exists but couldn't be retrieved") from None
            else:
                print(f"❌ Error creating policy engine: {error_code} - {error_message}")
                raise

    def _wait_for_policy_engine_active(self, policy_engine_id: str, max_wait: int = 300) -> None:
        """Wait for policy engine to become active.

        Args:
            policy_engine_id: The policy engine ID
            max_wait: Maximum time to wait in seconds
        """
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                response = self.control_client.get_policy_engine(policyEngineId=policy_engine_id)

                status = response["status"]
                print(f"Policy engine status: {status}")

                if status == "ACTIVE":
                    return
                elif status in ["CREATE_FAILED", "DELETE_FAILED"]:
                    raise RuntimeError(f"Policy engine creation failed with status: {status}")

                time.sleep(5)

            except ClientError as e:
                print(f"Error checking policy engine status: {e}")
                time.sleep(5)

        raise TimeoutError(f"Policy engine did not become active within {max_wait} seconds")

    def provision_policy(self, gateway_id: str, policy_name: str = "RenewalPeriodConstraintPolicy") -> dict[str, Any]:
        """Provision the AgentCore policy and attach it to the gateway.

        Args:
            gateway_id: The AgentCore Gateway identifier
            policy_name: Name for the policy

        Returns:
            Dictionary containing policy creation results
        """
        try:
            # First, get gateway details to get the ARN
            print(f"Getting gateway details for: {gateway_id}")
            gateway_response = self.control_client.get_gateway(gatewayIdentifier=gateway_id)
            gateway_arn = gateway_response["gatewayArn"]
            gateway_name = gateway_response["name"]

            print(f"Gateway ARN: {gateway_arn}")
            print(f"Gateway Name: {gateway_name}")

            # Create or get policy engine
            policy_engine = self.create_or_get_policy_engine()
            policy_engine_id = policy_engine["policyEngineId"]
            policy_engine_arn = policy_engine["policyEngineArn"]

            # Create the Cedar policy document
            cedar_policy = self.create_renewal_period_policy(gateway_arn)

            print(f"\nCreating AgentCore policy: {policy_name}")
            print(f"Policy Engine ID: {policy_engine_id}")
            print(f"Cedar policy document:\n{cedar_policy}\n")

            # Create the policy
            policy_response = self.control_client.create_policy(
                policyEngineId=policy_engine_id,
                name=policy_name,
                description="Enforces 30-day maximum renewal period for library books",
                definition={"cedar": {"statement": cedar_policy}},
                validationMode="FAIL_ON_ANY_FINDINGS",
            )

            policy_id = policy_response["policyId"]
            print(f"✅ Policy created successfully with ID: {policy_id}")

            # Wait for policy to become active
            print("Waiting for policy to become active...")
            self._wait_for_policy_active(policy_engine_id, policy_id)

            # Attach the policy engine to the gateway
            print(f"\nAttaching policy engine to gateway: {gateway_id}")

            # Get current gateway configuration
            current_gateway = self.control_client.get_gateway(gatewayIdentifier=gateway_id)

            # Update gateway with policy engine configuration
            update_response = self.control_client.update_gateway(
                gatewayIdentifier=gateway_id,
                name=current_gateway["name"],
                roleArn=current_gateway["roleArn"],
                authorizerType=current_gateway["authorizerType"],
                authorizerConfiguration=current_gateway["authorizerConfiguration"],
                protocolType=current_gateway["protocolType"],
                policyEngineConfiguration={
                    "arn": policy_engine_arn,
                    "mode": "ENFORCE",  # Use ENFORCE mode for production
                },
            )

            print("✅ Policy engine attached to gateway successfully")

            # Wait for gateway update to complete
            print("Waiting for gateway update to complete...")
            self._wait_for_gateway_active(gateway_id)

            return {
                "policy_id": policy_id,
                "policy_name": policy_name,
                "policy_engine_id": policy_engine_id,
                "policy_engine_arn": policy_engine_arn,
                "gateway_id": gateway_id,
                "gateway_arn": gateway_arn,
                "cedar_policy": cedar_policy,
                "policy_response": policy_response,
                "gateway_update_response": update_response,
            }

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]

            if error_code == "ConflictException":
                print(f"⚠️  Policy with name '{policy_name}' already exists")
                # Try to handle existing policy
                return self._handle_existing_policy(gateway_id, policy_name)
            else:
                print(f"❌ Error creating/attaching policy: {error_code} - {error_message}")
                raise

        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            raise

    def _wait_for_policy_active(self, policy_engine_id: str, policy_id: str, max_wait: int = 300) -> None:
        """Wait for policy to become active.

        Args:
            policy_engine_id: The policy engine ID
            policy_id: The policy ID
            max_wait: Maximum time to wait in seconds
        """
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                response = self.control_client.get_policy(policyEngineId=policy_engine_id, policyId=policy_id)

                status = response["status"]
                print(f"Policy status: {status}")

                if status == "ACTIVE":
                    return
                elif status in ["CREATE_FAILED", "UPDATE_FAILED"]:
                    status_reasons = response.get("statusReasons", [])
                    raise RuntimeError(f"Policy creation failed with status: {status}, reasons: {status_reasons}")

                time.sleep(5)

            except ClientError as e:
                print(f"Error checking policy status: {e}")
                time.sleep(5)

        raise TimeoutError(f"Policy did not become active within {max_wait} seconds")

    def _wait_for_gateway_active(self, gateway_id: str, max_wait: int = 300) -> None:
        """Wait for gateway to become active after update.

        Args:
            gateway_id: The gateway ID
            max_wait: Maximum time to wait in seconds
        """
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                response = self.control_client.get_gateway(gatewayIdentifier=gateway_id)

                status = response["status"]
                print(f"Gateway status: {status}")

                if status == "ACTIVE":
                    return
                elif status in ["UPDATE_FAILED", "CREATE_FAILED"]:
                    status_reasons = response.get("statusReasons", [])
                    raise RuntimeError(f"Gateway update failed with status: {status}, reasons: {status_reasons}")

                time.sleep(5)

            except ClientError as e:
                print(f"Error checking gateway status: {e}")
                time.sleep(5)

        raise TimeoutError(f"Gateway did not become active within {max_wait} seconds")

    def _handle_existing_policy(self, gateway_id: str, policy_name: str) -> dict[str, Any]:
        """Handle case where policy already exists.

        Args:
            gateway_id: The AgentCore Gateway identifier
            policy_name: Name of the existing policy

        Returns:
            Dictionary containing policy information
        """
        try:
            # Get policy engine
            policy_engine = self.create_or_get_policy_engine()
            policy_engine_id = policy_engine["policyEngineId"]
            policy_engine_arn = policy_engine["policyEngineArn"]

            # List policies to find the existing one
            policies_response = self.control_client.list_policies(policyEngineId=policy_engine_id)

            existing_policy = None
            for policy in policies_response.get("policies", []):
                if policy["name"] == policy_name:
                    existing_policy = policy
                    break

            if not existing_policy:
                raise ValueError(f"Policy '{policy_name}' not found in policy engine")

            policy_id = existing_policy["policyId"]
            print(f"Found existing policy with ID: {policy_id}")

            # Try to attach policy engine to gateway (might already be attached)
            try:
                gateway_response = self.control_client.get_gateway(gatewayIdentifier=gateway_id)

                update_response = self.control_client.update_gateway(
                    gatewayIdentifier=gateway_id,
                    name=gateway_response["name"],
                    roleArn=gateway_response["roleArn"],
                    authorizerType=gateway_response["authorizerType"],
                    authorizerConfiguration=gateway_response["authorizerConfiguration"],
                    protocolType=gateway_response["protocolType"],
                    policyEngineConfiguration={
                        "arn": policy_engine_arn,
                        "mode": "ENFORCE",
                    },
                )
                print("✅ Policy engine attached to gateway")
            except ClientError as attach_error:
                if "already configured" in str(attach_error).lower():
                    print("ℹ️  Policy engine already attached to gateway")
                    update_response = {"message": "Policy engine already attached"}
                else:
                    raise

            return {
                "policy_id": policy_id,
                "policy_name": policy_name,
                "policy_engine_id": policy_engine_id,
                "policy_engine_arn": policy_engine_arn,
                "gateway_id": gateway_id,
                "cedar_policy": self.create_renewal_period_policy("existing"),
                "policy_response": {"message": "Policy already existed"},
                "gateway_update_response": update_response,
            }

        except Exception as e:
            print(f"❌ Error handling existing policy: {str(e)}")
            raise

    def verify_policy_attachment(self, gateway_id: str) -> bool:
        """Verify that policies are properly attached to the gateway.

        Args:
            gateway_id: The AgentCore Gateway identifier

        Returns:
            True if policies are attached, False otherwise
        """
        try:
            # Get gateway details to check attached policy engine
            response = self.control_client.get_gateway(gatewayIdentifier=gateway_id)

            policy_engine_config = response.get("policyEngineConfiguration")

            print(f"Gateway status: {response.get('status', 'Unknown')}")

            if policy_engine_config:
                policy_engine_arn = policy_engine_config.get("arn")
                mode = policy_engine_config.get("mode")

                print("✅ Policy engine attached to gateway:")
                print(f"  - ARN: {policy_engine_arn}")
                print(f"  - Mode: {mode}")

                return True
            else:
                print("⚠️  No policy engine found attached to gateway")
                print(f"Gateway response keys: {list(response.keys())}")
                return False

        except Exception as e:
            print(f"❌ Error verifying policy attachment: {str(e)}")
            return False


def main() -> None:
    """Main function to provision AgentCore policy."""
    if len(sys.argv) < 2:
        print("Usage: python provision_policy.py <gateway_id> [region]")
        print("Example: python provision_policy.py gw-abc123def456 us-west-2")
        sys.exit(1)

    gateway_id = sys.argv[1]
    region = sys.argv[2] if len(sys.argv) > 2 else "us-east-1"

    print("🚀 Starting AgentCore policy provisioning...")
    print(f"Gateway ID: {gateway_id}")
    print(f"Region: {region}\n")

    try:
        provisioner = AgentCorePolicyProvisioner(region=region)

        # Provision the policy
        result = provisioner.provision_policy(gateway_id)

        # Verify the attachment
        print("\n🔍 Verifying policy attachment...")
        verification_success = provisioner.verify_policy_attachment(gateway_id)

        if verification_success:
            print("\n✅ Policy provisioning completed successfully!")
            print(f"Policy ID: {result['policy_id']}")
            print(f"Policy Engine ID: {result['policy_engine_id']}")
            print(f"Gateway ID: {result['gateway_id']}")
        else:
            print("\n⚠️  Policy provisioning completed but verification failed")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Policy provisioning failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
