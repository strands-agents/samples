# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""S3 Tables tools for the DataProcessing Agent."""

from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError
from strands import tool


def create_s3tables_tools():
    """Create and return S3 Tables tools"""
    from botocore.exceptions import ClientError

    @tool
    def manage_s3_table_buckets(
        operation: str,
        table_bucket_name: str = None,
        table_bucket_arn: str = None,
        encryption_configuration: dict = None,
        resource_policy: str = None,
        maintenance_type: str = None,
        maintenance_config: dict = None,
        prefix: str = None,
        max_buckets: int = None,
        continuation_token: str = None,
    ) -> str:
        """
        Manage S3 Table Buckets with comprehensive operations.

        Operations:
        - create_table_bucket: Create a new table bucket
        - delete_table_bucket: Delete an existing table bucket
        - get_table_bucket: Get details about a table bucket
        - list_table_buckets: List all table buckets
        - put_table_bucket_encryption: Set encryption configuration
        - get_table_bucket_encryption: Get encryption configuration
        - delete_table_bucket_encryption: Delete encryption configuration
        - put_table_bucket_policy: Set bucket policy
        - get_table_bucket_policy: Get bucket policy
        - delete_table_bucket_policy: Delete bucket policy
        - put_table_bucket_maintenance_configuration: Set maintenance configuration
        - get_table_bucket_maintenance_configuration: Get maintenance configuration

        Args:
            operation: The operation to perform
            table_bucket_name: Name of the table bucket (for create operations)
            table_bucket_arn: ARN of the table bucket (for most operations)
            encryption_configuration: Encryption settings (dict with sseAlgorithm and optional kmsKeyArn)
            resource_policy: JSON policy document as string
            maintenance_type: Type of maintenance (e.g., 'icebergUnreferencedFileRemoval')
            maintenance_config: Maintenance configuration dict
            prefix: Prefix filter for list operations
            max_buckets: Maximum number of buckets to return
            continuation_token: Token for pagination
        """
        try:
            # Create S3 Tables client
            s3tables_client = boto3.client(
                "s3tables", region_name=os.getenv("AWS_REGION", "us-east-1")
            )

            if operation == "create_table_bucket":
                if not table_bucket_name:
                    return "❌ Error: table_bucket_name is required for create_table_bucket operation"

                params = {"name": table_bucket_name}
                if encryption_configuration:
                    params["encryptionConfiguration"] = json.dumps(
                        encryption_configuration
                    )

                response = s3tables_client.create_table_bucket(**params)
                return f"✅ Table bucket created successfully! ARN: {response['arn']}"

            elif operation == "delete_table_bucket":
                if not table_bucket_arn:
                    return "❌ Error: table_bucket_arn is required for delete_table_bucket operation"

                s3tables_client.delete_table_bucket(tableBucketARN=table_bucket_arn)
                return f"✅ Table bucket {table_bucket_arn} deleted successfully!"

            elif operation == "get_table_bucket":
                if not table_bucket_arn:
                    return "❌ Error: table_bucket_arn is required for get_table_bucket operation"

                response = s3tables_client.get_table_bucket(
                    tableBucketARN=table_bucket_arn
                )
                return (
                    f"✅ Table bucket details:\n"
                    + f"Name: {response['name']}\n"
                    + f"ARN: {response['arn']}\n"
                    + f"Owner Account ID: {response['ownerAccountId']}\n"
                    + f"Created At: {response['createdAt']}\n"
                    + f"Table Bucket ID: {response.get('tableBucketId', 'N/A')}"
                )

            elif operation == "list_table_buckets":
                params = {}
                if prefix:
                    params["prefix"] = prefix
                if max_buckets:
                    params["maxBuckets"] = max_buckets
                if continuation_token:
                    params["continuationToken"] = continuation_token

                response = s3tables_client.list_table_buckets(**params)
                buckets = response.get("tableBuckets", [])

                result = f"✅ Found {len(buckets)} table buckets:\n"
                for bucket in buckets:
                    result += f"- {bucket['name']} (ARN: {bucket['arn']}, Created: {bucket['createdAt']})\n"

                if response.get("continuationToken"):
                    result += f"\nContinuation Token: {response['continuationToken']}"

                return result

            elif operation == "put_table_bucket_encryption":
                if not table_bucket_arn or not encryption_configuration:
                    return "❌ Error: table_bucket_arn and encryption_configuration are required"

                s3tables_client.put_table_bucket_encryption(
                    tableBucketARN=table_bucket_arn,
                    encryptionConfiguration=encryption_configuration,
                )
                return f"✅ Encryption configuration set for table bucket {table_bucket_arn}"

            elif operation == "get_table_bucket_encryption":
                if not table_bucket_arn:
                    return "❌ Error: table_bucket_arn is required"

                response = s3tables_client.get_table_bucket_encryption(
                    tableBucketARN=table_bucket_arn
                )
                config = response["encryptionConfiguration"]
                result = f"✅ Encryption configuration for {table_bucket_arn}:\n"
                result += f"Algorithm: {config['sseAlgorithm']}\n"
                if config.get("kmsKeyArn"):
                    result += f"KMS Key ARN: {config['kmsKeyArn']}\n"
                return result

            elif operation == "delete_table_bucket_encryption":
                if not table_bucket_arn:
                    return "❌ Error: table_bucket_arn is required"

                s3tables_client.delete_table_bucket_encryption(
                    tableBucketARN=table_bucket_arn
                )
                return f"✅ Encryption configuration deleted for table bucket {table_bucket_arn}"

            elif operation == "put_table_bucket_policy":
                if not table_bucket_arn or not resource_policy:
                    return "❌ Error: table_bucket_arn and resource_policy are required"

                s3tables_client.put_table_bucket_policy(
                    tableBucketARN=table_bucket_arn, resourcePolicy=resource_policy
                )
                return f"✅ Policy set for table bucket {table_bucket_arn}"

            elif operation == "get_table_bucket_policy":
                if not table_bucket_arn:
                    return "❌ Error: table_bucket_arn is required"

                response = s3tables_client.get_table_bucket_policy(
                    tableBucketARN=table_bucket_arn
                )
                return (
                    f"✅ Policy for {table_bucket_arn}:\n{response['resourcePolicy']}"
                )

            elif operation == "delete_table_bucket_policy":
                if not table_bucket_arn:
                    return "❌ Error: table_bucket_arn is required"

                s3tables_client.delete_table_bucket_policy(
                    tableBucketARN=table_bucket_arn
                )
                return f"✅ Policy deleted for table bucket {table_bucket_arn}"

            elif operation == "put_table_bucket_maintenance_configuration":
                if (
                    not table_bucket_arn
                    or not maintenance_type
                    or not maintenance_config
                ):
                    return "❌ Error: table_bucket_arn, maintenance_type, and maintenance_config are required"

                s3tables_client.put_table_bucket_maintenance_configuration(
                    tableBucketARN=table_bucket_arn,
                    type=maintenance_type,
                    value=maintenance_config,
                )
                return f"✅ Maintenance configuration set for table bucket {table_bucket_arn}"

            elif operation == "get_table_bucket_maintenance_configuration":
                if not table_bucket_arn:
                    return "❌ Error: table_bucket_arn is required"

                response = s3tables_client.get_table_bucket_maintenance_configuration(
                    tableBucketARN=table_bucket_arn
                )
                config = response["configuration"]
                result = f"✅ Maintenance configuration for {table_bucket_arn}:\n"
                for config_type, config_value in config.items():
                    result += f"Type: {config_type}\n"
                    result += f"Status: {config_value.get('status', 'N/A')}\n"
                    if config_value.get("settings"):
                        result += f"Settings: {config_value['settings']}\n"
                return result

            else:
                return f"❌ Error: Unknown operation '{operation}'"

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            return f"❌ AWS Error ({error_code}): {error_message}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    @tool
    def manage_s3_namespaces(
        operation: str,
        table_bucket_arn: str,
        namespace: str = None,
        prefix: str = None,
        max_namespaces: int = None,
        continuation_token: str = None,
    ) -> str:
        """
        Manage S3 Tables Namespaces.

        Operations:
        - create_namespace: Create a new namespace
        - delete_namespace: Delete an existing namespace
        - get_namespace: Get details about a namespace
        - list_namespaces: List all namespaces in a table bucket

        Args:
            operation: The operation to perform
            table_bucket_arn: ARN of the table bucket
            namespace: Name of the namespace
            prefix: Prefix filter for list operations
            max_namespaces: Maximum number of namespaces to return
            continuation_token: Token for pagination
        """
        try:
            s3tables_client = boto3.client(
                "s3tables", region_name=os.getenv("AWS_REGION", "us-east-1")
            )

            if operation == "create_namespace":
                if not namespace:
                    return (
                        "❌ Error: namespace is required for create_namespace operation"
                    )

                response = s3tables_client.create_namespace(
                    tableBucketARN=table_bucket_arn, namespace=[namespace]
                )
                return f"✅ Namespace '{namespace}' created successfully in {table_bucket_arn}"

            elif operation == "delete_namespace":
                if not namespace:
                    return (
                        "❌ Error: namespace is required for delete_namespace operation"
                    )

                s3tables_client.delete_namespace(
                    tableBucketARN=table_bucket_arn, namespace=namespace
                )
                return f"✅ Namespace '{namespace}' deleted successfully from {table_bucket_arn}"

            elif operation == "get_namespace":
                if not namespace:
                    return "❌ Error: namespace is required for get_namespace operation"

                response = s3tables_client.get_namespace(
                    tableBucketARN=table_bucket_arn, namespace=namespace
                )
                return (
                    f"✅ Namespace details:\n"
                    + f"Name: {response['namespace']}\n"
                    + f"Created At: {response['createdAt']}\n"
                    + f"Created By: {response['createdBy']}\n"
                    + f"Owner Account ID: {response['ownerAccountId']}\n"
                    + f"Namespace ID: {response.get('namespaceId', 'N/A')}\n"
                    + f"Table Bucket ID: {response.get('tableBucketId', 'N/A')}"
                )

            elif operation == "list_namespaces":
                params = {"tableBucketARN": table_bucket_arn}
                if prefix:
                    params["prefix"] = prefix
                if max_namespaces:
                    params["maxNamespaces"] = max_namespaces
                if continuation_token:
                    params["continuationToken"] = continuation_token

                response = s3tables_client.list_namespaces(**params)
                namespaces = response.get("namespaces", [])

                result = (
                    f"✅ Found {len(namespaces)} namespaces in {table_bucket_arn}:\n"
                )
                for ns in namespaces:
                    result += f"- {ns['namespace']} (Created: {ns['createdAt']}, Owner: {ns['ownerAccountId']})\n"

                if response.get("continuationToken"):
                    result += f"\nContinuation Token: {response['continuationToken']}"

                return result

            else:
                return f"❌ Error: Unknown operation '{operation}'"

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            return f"❌ AWS Error ({error_code}): {error_message}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    @tool
    def manage_s3_tables(
        operation: str,
        table_bucket_arn: str = None,
        namespace: str = None,
        table_name: str = None,
        table_arn: str = None,
        table_format: str = None,
        table_metadata: dict = None,
        encryption_configuration: dict = None,
        resource_policy: str = None,
        maintenance_type: str = None,
        maintenance_config: dict = None,
        new_namespace_name: str = None,
        new_table_name: str = None,
        version_token: str = None,
        metadata_location: str = None,
        prefix: str = None,
        max_tables: int = None,
        continuation_token: str = None,
    ) -> str:
        """
        Manage S3 Tables with comprehensive operations.

        Operations:
        - create_table: Create a new table
        - delete_table: Delete an existing table
        - get_table: Get details about a table
        - list_tables: List all tables in a namespace or table bucket
        - rename_table: Rename a table or move it to a different namespace
        - get_table_encryption: Get table encryption configuration
        - put_table_policy: Set table policy
        - get_table_policy: Get table policy
        - delete_table_policy: Delete table policy
        - put_table_maintenance_configuration: Set table maintenance configuration
        - get_table_maintenance_configuration: Get table maintenance configuration
        - get_table_maintenance_job_status: Get maintenance job status
        - get_table_metadata_location: Get table metadata location
        - update_table_metadata_location: Update table metadata location

        Args:
            operation: The operation to perform
            table_bucket_arn: ARN of the table bucket
            namespace: Name of the namespace
            table_name: Name of the table
            table_arn: ARN of the table (alternative to table_bucket_arn + namespace + table_name)
            table_format: Format of the table (e.g., 'ICEBERG')
            table_metadata: Table metadata dictionary
            encryption_configuration: Encryption settings
            resource_policy: JSON policy document as string
            maintenance_type: Type of maintenance
            maintenance_config: Maintenance configuration dict
            new_namespace_name: New namespace name for rename operation
            new_table_name: New table name for rename operation
            version_token: Version token for operations that require it
            metadata_location: Metadata location for update operations
            prefix: Prefix filter for list operations
            max_tables: Maximum number of tables to return
            continuation_token: Token for pagination
        """
        try:
            s3tables_client = boto3.client(
                "s3tables", region_name=os.getenv("AWS_REGION", "us-east-1")
            )

            if operation == "create_table":
                if not all([table_bucket_arn, namespace, table_name, table_format]):
                    return "❌ Error: table_bucket_arn, namespace, table_name, and table_format are required"

                params = {
                    "tableBucketARN": table_bucket_arn,
                    "namespace": namespace,
                    "name": table_name,
                    "format": table_format,
                }
                if table_metadata:
                    params["metadata"] = json.dumps(table_metadata)
                if encryption_configuration:
                    params["encryptionConfiguration"] = json.dumps(
                        encryption_configuration
                    )

                response = s3tables_client.create_table(**params)
                return (
                    f"✅ Table '{table_name}' created successfully!\n"
                    + f"Table ARN: {response['tableARN']}\n"
                    + f"Version Token: {response['versionToken']}"
                )

            elif operation == "delete_table":
                if not all([table_bucket_arn, namespace, table_name]):
                    return "❌ Error: table_bucket_arn, namespace, and table_name are required"

                params = {
                    "tableBucketARN": table_bucket_arn,
                    "namespace": namespace,
                    "name": table_name,
                }
                if version_token:
                    params["versionToken"] = version_token

                s3tables_client.delete_table(**params)
                return f"✅ Table '{table_name}' deleted successfully from namespace '{namespace}'"

            elif operation == "get_table":
                if table_arn:
                    params = {"tableArn": table_arn}
                elif all([table_bucket_arn, namespace, table_name]):
                    params = {
                        "tableBucketARN": table_bucket_arn,
                        "namespace": namespace,
                        "name": table_name,
                    }
                else:
                    return "❌ Error: Either table_arn OR (table_bucket_arn + namespace + table_name) is required"

                response = s3tables_client.get_table(**params)
                return (
                    f"✅ Table details:\n"
                    + f"Name: {response['name']}\n"
                    + f"Type: {response['type']}\n"
                    + f"Table ARN: {response['tableARN']}\n"
                    + f"Namespace: {response['namespace']}\n"
                    + f"Format: {response['format']}\n"
                    + f"Version Token: {response['versionToken']}\n"
                    + f"Created At: {response['createdAt']}\n"
                    + f"Modified At: {response['modifiedAt']}\n"
                    + f"Owner Account ID: {response['ownerAccountId']}\n"
                    + f"Warehouse Location: {response['warehouseLocation']}\n"
                    + f"Metadata Location: {response.get('metadataLocation', 'N/A')}"
                )

            elif operation == "list_tables":
                if not table_bucket_arn:
                    return "❌ Error: table_bucket_arn is required"

                params = {"tableBucketARN": table_bucket_arn}
                if namespace:
                    params["namespace"] = namespace
                if prefix:
                    params["prefix"] = prefix
                if max_tables:
                    params["maxTables"] = max_tables
                if continuation_token:
                    params["continuationToken"] = continuation_token

                response = s3tables_client.list_tables(**params)
                tables = response.get("tables", [])

                result = f"✅ Found {len(tables)} tables in {table_bucket_arn}"
                if namespace:
                    result += f" (namespace: {namespace})"
                result += ":\n"

                for table in tables:
                    result += (
                        f"- {table['name']} (Namespace: {table['namespace']}, "
                        + f"Type: {table['type']}, Created: {table['createdAt']})\n"
                    )

                if response.get("continuationToken"):
                    result += f"\nContinuation Token: {response['continuationToken']}"

                return result

            else:
                return f"❌ Error: Unknown operation '{operation}'"

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            return f"❌ AWS Error ({error_code}): {error_message}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    return [manage_s3_table_buckets, manage_s3_namespaces, manage_s3_tables]
