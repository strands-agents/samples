import json
import boto3
import time
import uuid
from botocore.exceptions import ClientError
from opensearchpy import (
    OpenSearch,
    RequestsHttpConnection,
    AWSV4SignerAuth,
    RequestError,
)
import pprint
import random
import yaml
import os
import argparse

valid_embedding_models = [
    "cohere.embed-multilingual-v3",
    "cohere.embed-english-v3",
    "amazon.titan-embed-text-v1",
    "amazon.titan-embed-text-v2:0",
]
pp = pprint.PrettyPrinter(indent=2)


def read_yaml_file(file_path: str):
    """
    read and process a yaml file
    Args:
        file_path: the path to the yaml file
    """
    with open(file_path, "r") as file:
        try:
            return yaml.safe_load(file)
        except yaml.YAMLError as e:
            print(f"Error reading YAML file: {e}")
            return None


def interactive_sleep(seconds: int):
    """
    Support functionality to induce an artificial 'sleep' to the code in order to wait for resources to be available
    Args:
        seconds (int): number of seconds to sleep for
    """
    dots = ""
    for i in range(seconds):
        dots += "."
        print(dots, end="\r")
        time.sleep(1)


def wait_for_collection_creation(client, oss_collection_name: str) -> str:
    """Waits for the collection to become active"""
    response = client.batch_get_collection(names=[oss_collection_name])
    # Periodically check collection status
    while (response["collectionDetails"][0]["status"]) == "CREATING":
        print("Creating collection...")
        time.sleep(30)
        response = client.batch_get_collection(names=[oss_collection_name])
    print("\nCollection successfully created:")
    print(response["collectionDetails"])
    # Extract the collection endpoint from the response
    host = response["collectionDetails"][0]["collectionEndpoint"]
    final_host = host.replace("https://", "")
    return final_host


class OpensearchServerless:

    def __init__(self, suffix=None):
        """
        Initialize clients for OpenSearch serverless
        """
        boto3_session = boto3.session.Session()
        self.region_name = boto3_session.region_name
        self.iam_client = boto3_session.client("iam", region_name=self.region_name)
        self.account_number = (
            boto3.client("sts", region_name=self.region_name)
            .get_caller_identity()
            .get("Account")
        )
        self.suffix = suffix if suffix else str(uuid.uuid4())[:4]
        self.identity = boto3.client(
            "sts", region_name=self.region_name
        ).get_caller_identity()["Arn"]
        self.aoss_client = boto3_session.client(
            "opensearchserverless", region_name=self.region_name
        )
        self.s3_client = boto3.client("s3", region_name=self.region_name)
        credentials = boto3.Session().get_credentials()
        self.awsauth = AWSV4SignerAuth(credentials, self.region_name, "aoss")
        self.oss_client = None
        self.data_bucket_name = None
        # Don't automatically create OSS in init
        self.collection_id = None
        self.collection_arn = None
        self.encryption_policy_name = None
        self.network_policy_name = None
        self.access_policy_name = None

    def create_aoss(self, vector_store_name: str, description: str = "OSS Collection"):
        """
        Create OpenSearch Serverless Collection. If already existent, retrieve
        Args:
            vector_store_name: name of the vector store
            description: description for the collection
        """
        # Check if the collection already exists
        try:
            existing_collections = self.aoss_client.batch_get_collection(
                names=[vector_store_name]
            )
            if existing_collections["collectionDetails"]:
                # Collection already exists, just return the host and ID
                collection = existing_collections["collectionDetails"][0]
                self.collection_id = collection["id"]
                host = collection["collectionEndpoint"].replace("https://", "")
                print(
                    f"Collection {vector_store_name} already exists, using existing collection."
                )
                return host, None, self.collection_id, None
        except Exception:
            # Collection doesn't exist or error occurred, proceed with creation
            pass

        # Generate unique policy names with timestamp to avoid conflicts
        timestamp = int(time.time())
        self.encryption_policy_name = f"{vector_store_name}-sp-{timestamp}"
        self.network_policy_name = f"{vector_store_name}-np-{timestamp}"
        self.access_policy_name = f"{vector_store_name}-ap-{timestamp}"

        # Create a mock role for the bedrock execution role
        bedrock_kb_execution_role = {
            "Role": {"Arn": self.identity}  # Use the current identity as a fallback
        }

        # Create policies first
        try:
            encryption_policy, network_policy, access_policy = (
                self.create_policies_in_oss(
                    self.encryption_policy_name,
                    vector_store_name,
                    self.network_policy_name,
                    bedrock_kb_execution_role,
                    self.access_policy_name,
                )
            )

            # Wait a moment for policies to propagate
            print("Waiting for policies to propagate...")
            time.sleep(5)

            # Now create the collection
            collection = self.aoss_client.create_collection(
                name=vector_store_name, type="VECTORSEARCH", description=description
            )
            self.collection_id = collection["createCollectionDetail"]["id"]
            self.collection_arn = collection["createCollectionDetail"]["arn"]
            host = wait_for_collection_creation(self.aoss_client, vector_store_name)
            return host, collection, self.collection_id, self.collection_arn

        except Exception as e:
            print(f"Error creating policies or collection: {e}")
            # Clean up any policies that might have been created
            self.cleanup_policies()
            raise

    def create_vector_index(self, index_name: str):
        """
        Create OpenSearch Serverless vector index. If existent, ignore
        Args:
            index_name: name of the vector index
        """
        body_json = {
            "settings": {
                "index.knn": "true",
                "number_of_shards": 1,
                "knn.algo_param.ef_search": 512,
                "number_of_replicas": 0,
            },
            "mappings": {
                "properties": {
                    "vector": {
                        "type": "knn_vector",
                        "dimension": 1024,
                        "method": {
                            "name": "hnsw",
                            "engine": "faiss",
                            "space_type": "l2",
                        },
                    },
                    "text": {"type": "text"},
                    "text-metadata": {"type": "text"},
                }
            },
        }

        # Create index
        try:
            response = self.oss_client.indices.create(
                index=index_name, body=json.dumps(body_json)
            )
            print("\nCreating index:")
            pp.pprint(response)

            # index creation can take up to a minute
            interactive_sleep(60)
        except RequestError as e:
            # you can delete the index if its already exists
            # oss_client.indices.delete(index=index_name)
            print(
                f"Error while trying to create the index, with error {e.error}\nyou may unmark the delete above to "
                f"delete, and recreate the index"
            )

    def create_policies_in_oss(
        self,
        encryption_policy_name: str,
        vector_store_name: str,
        network_policy_name: str,
        bedrock_kb_execution_role: dict,
        access_policy_name: str,
    ):
        """
        Create OpenSearch Serverless encryption, network and data access policies.
        If policies already exist, retrieve them
        Args:
            encryption_policy_name: name of the data encryption policy
            vector_store_name: name of the vector store
            network_policy_name: name of the network policy
            bedrock_kb_execution_role: dictionary containing role information
            access_policy_name: name of the data access policy

        Returns:
            encryption_policy, network_policy, access_policy
        """
        try:
            encryption_policy = self.aoss_client.create_security_policy(
                name=encryption_policy_name,
                policy=json.dumps(
                    {
                        "Rules": [
                            {
                                "Resource": ["collection/" + vector_store_name],
                                "ResourceType": "collection",
                            }
                        ],
                        "AWSOwnedKey": True,
                    }
                ),
                type="encryption",
            )
        except self.aoss_client.exceptions.ConflictException:
            print(f"{encryption_policy_name} already exists, retrieving it!")
            encryption_policy = self.aoss_client.get_security_policy(
                name=encryption_policy_name, type="encryption"
            )

        try:
            network_policy = self.aoss_client.create_security_policy(
                name=network_policy_name,
                policy=json.dumps(
                    [
                        {
                            "Rules": [
                                {
                                    "Resource": ["collection/" + vector_store_name],
                                    "ResourceType": "collection",
                                }
                            ],
                            "AllowFromPublic": True,
                        }
                    ]
                ),
                type="network",
            )
        except self.aoss_client.exceptions.ConflictException:
            print(f"{network_policy_name} already exists, retrieving it!")
            network_policy = self.aoss_client.get_security_policy(
                name=network_policy_name, type="network"
            )

        try:
            # Ensure principals are unique
            principals = []
            if self.identity:
                principals.append(self.identity)

            # Only add bedrock role if it's different from current identity
            if bedrock_kb_execution_role and "Role" in bedrock_kb_execution_role:
                role_arn = bedrock_kb_execution_role["Role"]["Arn"]
                if role_arn != self.identity and role_arn not in principals:
                    principals.append(role_arn)

            access_policy = self.aoss_client.create_access_policy(
                name=access_policy_name,
                policy=json.dumps(
                    [
                        {
                            "Rules": [
                                {
                                    "Resource": ["collection/" + vector_store_name],
                                    "Permission": [
                                        "aoss:CreateCollectionItems",
                                        "aoss:DeleteCollectionItems",
                                        "aoss:UpdateCollectionItems",
                                        "aoss:DescribeCollectionItems",
                                    ],
                                    "ResourceType": "collection",
                                },
                                {
                                    "Resource": ["index/" + vector_store_name + "/*"],
                                    "Permission": [
                                        "aoss:CreateIndex",
                                        "aoss:DeleteIndex",
                                        "aoss:UpdateIndex",
                                        "aoss:DescribeIndex",
                                        "aoss:ReadDocument",
                                        "aoss:WriteDocument",
                                    ],
                                    "ResourceType": "index",
                                },
                            ],
                            "Principal": principals,
                            "Description": "Easy data policy",
                        }
                    ]
                ),
                type="data",
            )
        except self.aoss_client.exceptions.ConflictException:
            print(f"{access_policy_name} already exists, retrieving it!")
            access_policy = self.aoss_client.get_access_policy(
                name=access_policy_name, type="data"
            )
        return encryption_policy, network_policy, access_policy

    def cleanup_policies(self):
        """
        Clean up any policies that might have been created
        """
        # Delete access policy if it exists
        if hasattr(self, "access_policy_name"):
            try:
                self.aoss_client.delete_access_policy(
                    type="data", name=self.access_policy_name
                )
                print(f"Access policy {self.access_policy_name} deleted successfully!")
            except Exception as e:
                print(f"Error deleting access policy: {e}")

        # Delete network policy if it exists
        if hasattr(self, "network_policy_name"):
            try:
                self.aoss_client.delete_security_policy(
                    type="network", name=self.network_policy_name
                )
                print(
                    f"Network policy {self.network_policy_name} deleted successfully!"
                )
            except Exception as e:
                print(f"Error deleting network policy: {e}")

        # Delete encryption policy if it exists
        if hasattr(self, "encryption_policy_name"):
            try:
                self.aoss_client.delete_security_policy(
                    type="encryption", name=self.encryption_policy_name
                )
                print(
                    f"Encryption policy {self.encryption_policy_name} deleted successfully!"
                )
            except Exception as e:
                print(f"Error deleting encryption policy: {e}")

    def delete_oss(self, collection_name, collection_id=None):
        """
        Delete OpenSearch Serverless collection and associated policies
        Args:
            collection_name: name of the collection to delete
            collection_id: optional collection ID if known
        """
        try:
            # Use instance variables if collection_id is not provided
            if collection_id is None and hasattr(self, "collection_id"):
                collection_id = self.collection_id

            if collection_id:
                self.aoss_client.delete_collection(id=collection_id)
                print(f"Collection {collection_name} deleted successfully!")
            else:
                # Try to get collection ID if not provided
                try:
                    collection = self.aoss_client.batch_get_collection(
                        names=[collection_name]
                    )["collectionDetails"][0]
                    collection_id = collection["id"]
                    self.aoss_client.delete_collection(id=collection_id)
                    print(f"Collection {collection_name} deleted successfully!")
                except Exception as e:
                    print(f"Could not find collection {collection_name}: {e}")

            # Wait for collection to be deleted before cleaning up policies
            print("Waiting for collection deletion to complete...")
            time.sleep(10)

            # Clean up policies
            self.cleanup_policies()

            print("OpenSearch Serverless resources cleanup completed!")
        except Exception as e:
            print(f"Error during OpenSearch Serverless cleanup: {e}")


def save_to_env_file(env_path, variables):
    """Save variables to .env file"""
    with open(env_path, "w") as f:
        for key, value in variables.items():
            f.write(f"{key}={value}\n")
    print(f"Environment variables saved to {env_path}")


def check_permissions():
    """Check if the current role has the necessary permissions"""
    try:
        # Create a minimal test policy to check permissions
        boto3_session = boto3.session.Session()
        aoss_client = boto3_session.client("opensearchserverless")

        # Just check if we can list collections (doesn't actually create anything)
        aoss_client.list_collections()
        return True
    except Exception as e:
        if "AccessDeniedException" in str(e):
            return False
        # If it's another type of error, we'll assume permissions are OK
        return True


if __name__ == "__main__":
    try:
        # Initialize clients
        ssm_client = boto3.client("ssm")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        env_file_path = os.path.join(parent_dir, ".env")

        # Load configuration
        config_path = f"{current_dir}/opensearch_config.yaml"
        data = read_yaml_file(config_path)

        if not data:
            print(f"Error: Could not read configuration from {config_path}")
            exit(1)

        parser = argparse.ArgumentParser(description="Opensearch Serverless handler")
        parser.add_argument(
            "--mode",
            required=True,
            help="Opensearch Serverless helper mode. Options: create or delete.",
        )
        parser.add_argument(
            "--manual",
            action="store_true",
            help="Create .env file with placeholder values for manual setup",
        )

        args = parser.parse_args()
        print(f"Configuration loaded: {data}")

        # Check if we're using manual mode
        if args.manual:
            print("Manual mode: Creating .env file with placeholder values")
            # Create .env file with placeholder values
            env_vars = {
                "OPENSEARCH_HOST": "<your-opensearch-host>.<region>.aoss.amazonaws.com",
                "OPENSEARCH_COLLECTION_NAME": data["opensearch_collection_name"],
                "OPENSEARCH_COLLECTION_ID": "placeholder_id",
            }
            save_to_env_file(env_file_path, env_vars)
            print(f"Environment variables saved to {env_file_path}")
            print(
                "Please update the .env file with your actual OpenSearch Serverless values"
            )
            exit(0)

        # Check permissions before proceeding
        if args.mode == "create" and not check_permissions():
            print(
                "\n⚠️ ERROR: Insufficient permissions to create OpenSearch Serverless resources"
            )
            print("\nYour IAM role needs the following permissions:")
            print("  - aoss:CreateSecurityPolicy")
            print("  - aoss:CreateCollection")
            print("  - aoss:CreateAccessPolicy")
            print("  - aoss:BatchGetCollection")
            print("\nOptions:")
            print("1. Update your IAM role with the necessary permissions")
            print(
                "2. Use the --manual flag to create a template .env file that you can fill in manually"
            )
            print(
                "3. Use an existing OpenSearch Serverless collection by setting OPENSEARCH_HOST in your environment"
            )
            exit(1)

        # Initialize OpenSearch Serverless client if we have permissions
        oss = OpensearchServerless()

        if args.mode == "create":
            print(
                f"Creating OpenSearch Serverless collection: {data['opensearch_collection_name']}"
            )
            try:
                host, collection, collection_id, collection_arn = oss.create_aoss(
                    data["opensearch_collection_name"],
                    data.get(
                        "opensearch_description", "Memory Persistent Agent Collection"
                    ),
                )

                # For existing collections, we only have host and ID
                # Save to .env file first (this is the minimum we need)
                env_vars = {
                    "OPENSEARCH_HOST": host,
                    "OPENSEARCH_COLLECTION_NAME": data["opensearch_collection_name"],
                    "OPENSEARCH_COLLECTION_ID": collection_id,
                }
                save_to_env_file(env_file_path, env_vars)

                # Only store additional parameters in SSM if we created a new collection
                if collection is not None and collection_arn is not None:
                    # Store parameters in SSM Parameter Store
                    params_to_store = {
                        "hostname": host,
                        "id": collection_id,
                        "arn": collection_arn,
                        "name": data["opensearch_collection_name"],
                        "encryption_policy": oss.encryption_policy_name,
                        "network_policy": oss.network_policy_name,
                        "access_policy": oss.access_policy_name,
                    }

                    # Store all parameters in SSM
                    for key, value in params_to_store.items():
                        if value is not None:  # Skip None values
                            ssm_client.put_parameter(
                                Name=f"{data['opensearch_collection_name']}-{key}",
                                Description=f"{data['opensearch_collection_name']} {key}",
                                Value=value,
                                Type="String",
                                Overwrite=True,
                            )

                print(f"OpenSearch Serverless collection setup completed!")
                print(f"\nOPENSEARCH_HOST: {host}")
                print(f"OPENSEARCH_COLLECTION_ID: {collection_id}\n")
                print(f"Environment variables saved to {env_file_path}")
            except Exception as e:
                print(f"Error creating OpenSearch resources: {e}")
                print("Try using --manual flag to create a template .env file")
                exit(1)

        elif args.mode == "delete":
            print(
                f"Deleting OpenSearch Serverless collection: {data['opensearch_collection_name']}"
            )

            # Get all parameters from SSM
            try:
                # Get collection ID
                collection_id = ssm_client.get_parameter(
                    Name=f"{data['opensearch_collection_name']}-id"
                )["Parameter"]["Value"]
                print(f"Found collection ID: {collection_id}")

                # Get policy names
                oss.encryption_policy_name = ssm_client.get_parameter(
                    Name=f"{data['opensearch_collection_name']}-encryption_policy"
                )["Parameter"]["Value"]

                oss.network_policy_name = ssm_client.get_parameter(
                    Name=f"{data['opensearch_collection_name']}-network_policy"
                )["Parameter"]["Value"]

                oss.access_policy_name = ssm_client.get_parameter(
                    Name=f"{data['opensearch_collection_name']}-access_policy"
                )["Parameter"]["Value"]

            except ssm_client.exceptions.ParameterNotFound as e:
                print(f"Warning: Some parameters not found in SSM: {e}")

            # Delete the collection
            try:
                oss.delete_oss(data["opensearch_collection_name"], collection_id)
            except Exception as e:
                print(f"Error deleting OpenSearch resources: {e}")

            # Clean up SSM parameters
            ssm_params = [
                "hostname",
                "id",
                "arn",
                "name",
                "encryption_policy",
                "network_policy",
                "access_policy",
            ]

            for param in ssm_params:
                try:
                    ssm_client.delete_parameter(
                        Name=f"{data['opensearch_collection_name']}-{param}"
                    )
                    print(
                        f"Deleted SSM parameter: {data['opensearch_collection_name']}-{param}"
                    )
                except ssm_client.exceptions.ParameterNotFound:
                    print(
                        f"SSM parameter {data['opensearch_collection_name']}-{param} not found"
                    )

            # Remove .env file if it exists
            if os.path.exists(env_file_path):
                os.remove(env_file_path)
                print(f"Removed .env file: {env_file_path}")

        else:
            print(f"Invalid mode: {args.mode}. Use 'create' or 'delete'.")
            exit(1)

    except Exception as e:
        print(f"Error: {e}")
        exit(1)
