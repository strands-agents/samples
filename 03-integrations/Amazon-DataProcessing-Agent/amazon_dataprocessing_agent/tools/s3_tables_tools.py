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


class S3TablesTools:
    """Tools for interacting with Amazon S3 Tables"""

    def __init__(self, region_name: str = "us-east-1"):
        """Initialize S3 Tables client"""
        self.s3tables_client = boto3.client("s3tables", region_name=region_name)
        self.region_name = region_name

    def list_table_buckets(self) -> List[Dict[str, Any]]:
        """List all S3 table buckets"""
        try:
            response = self.s3tables_client.list_table_buckets()
            return [
                {
                    "arn": bucket["arn"],
                    "name": bucket["name"],
                    "creation_date": bucket["createdAt"].isoformat(),
                    "owner_account_id": bucket["ownerAccountId"],
                }
                for bucket in response.get("tableBuckets", [])
            ]
        except ClientError as e:
            raise Exception(f"Error listing table buckets: {str(e)}")

    def create_table_bucket(self, name: str) -> Dict[str, Any]:
        """Create a new S3 table bucket"""
        try:
            response = self.s3tables_client.create_table_bucket(name=name)
            return {
                "arn": response["arn"],
                "name": name,
                "status": "created",
            }
        except ClientError as e:
            raise Exception(f"Error creating table bucket: {str(e)}")

    def delete_table_bucket(self, name: str) -> Dict[str, Any]:
        """Delete an S3 table bucket"""
        try:
            self.s3tables_client.delete_table_bucket(name=name)
            return {
                "name": name,
                "status": "deleted",
            }
        except ClientError as e:
            raise Exception(f"Error deleting table bucket: {str(e)}")

    def list_tables(self, table_bucket_arn: str) -> List[Dict[str, Any]]:
        """List tables in a table bucket"""
        try:
            response = self.s3tables_client.list_tables(tableBucketARN=table_bucket_arn)
            return [
                {
                    "arn": table["arn"],
                    "name": table["name"],
                    "type": table["type"],
                    "creation_date": table["createdAt"].isoformat(),
                    "modified_date": table["modifiedAt"].isoformat(),
                }
                for table in response.get("tables", [])
            ]
        except ClientError as e:
            raise Exception(f"Error listing tables: {str(e)}")

    def create_table(
        self,
        table_bucket_arn: str,
        name: str,
        format: str = "ICEBERG",
        schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new table in S3 Tables"""
        try:
            params = {
                "tableBucketARN": table_bucket_arn,
                "name": name,
                "format": format,
            }

            if schema:
                params["schema"] = schema

            response = self.s3tables_client.create_table(**params)
            return {
                "arn": response["arn"],
                "name": name,
                "format": format,
                "status": "created",
            }
        except ClientError as e:
            raise Exception(f"Error creating table: {str(e)}")

    def delete_table(self, table_bucket_arn: str, name: str) -> Dict[str, Any]:
        """Delete a table from S3 Tables"""
        try:
            self.s3tables_client.delete_table(
                tableBucketARN=table_bucket_arn, name=name
            )
            return {
                "table_bucket_arn": table_bucket_arn,
                "name": name,
                "status": "deleted",
            }
        except ClientError as e:
            raise Exception(f"Error deleting table: {str(e)}")

    def get_table(self, table_bucket_arn: str, name: str) -> Dict[str, Any]:
        """Get details about a specific table"""
        try:
            response = self.s3tables_client.get_table(
                tableBucketARN=table_bucket_arn, name=name
            )
            return {
                "arn": response["arn"],
                "name": response["name"],
                "type": response["type"],
                "format": response["format"],
                "creation_date": response["createdAt"].isoformat(),
                "modified_date": response["modifiedAt"].isoformat(),
                "version_token": response.get("versionToken"),
                "warehouse_location": response.get("warehouseLocation"),
            }
        except ClientError as e:
            raise Exception(f"Error getting table details: {str(e)}")

    def update_table_metadata_location(
        self,
        table_bucket_arn: str,
        name: str,
        metadata_location: str,
        version_token: str,
    ) -> Dict[str, Any]:
        """Update table metadata location"""
        try:
            response = self.s3tables_client.update_table_metadata_location(
                tableBucketARN=table_bucket_arn,
                name=name,
                metadataLocation=metadata_location,
                versionToken=version_token,
            )
            return {
                "name": name,
                "metadata_location": metadata_location,
                "version_token": response["versionToken"],
                "status": "updated",
            }
        except ClientError as e:
            raise Exception(f"Error updating table metadata location: {str(e)}")

    def rename_table(
        self, table_bucket_arn: str, name: str, new_name: str, version_token: str
    ) -> Dict[str, Any]:
        """Rename a table"""
        try:
            response = self.s3tables_client.rename_table(
                tableBucketARN=table_bucket_arn,
                name=name,
                newName=new_name,
                versionToken=version_token,
            )
            return {
                "old_name": name,
                "new_name": new_name,
                "version_token": response["versionToken"],
                "status": "renamed",
            }
        except ClientError as e:
            raise Exception(f"Error renaming table: {str(e)}")

    def get_table_bucket_policy(self, table_bucket_arn: str) -> Dict[str, Any]:
        """Get the policy for a table bucket"""
        try:
            response = self.s3tables_client.get_table_bucket_policy(
                tableBucketARN=table_bucket_arn
            )
            return {
                "table_bucket_arn": table_bucket_arn,
                "policy": response["policy"],
            }
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchTableBucketPolicy":
                return {
                    "table_bucket_arn": table_bucket_arn,
                    "policy": None,
                    "message": "No policy found for this table bucket",
                }
            raise Exception(f"Error getting table bucket policy: {str(e)}")

    def put_table_bucket_policy(
        self, table_bucket_arn: str, policy: str
    ) -> Dict[str, Any]:
        """Set the policy for a table bucket"""
        try:
            self.s3tables_client.put_table_bucket_policy(
                tableBucketARN=table_bucket_arn, policy=policy
            )
            return {
                "table_bucket_arn": table_bucket_arn,
                "status": "policy_updated",
            }
        except ClientError as e:
            raise Exception(f"Error setting table bucket policy: {str(e)}")

    def delete_table_bucket_policy(self, table_bucket_arn: str) -> Dict[str, Any]:
        """Delete the policy for a table bucket"""
        try:
            self.s3tables_client.delete_table_bucket_policy(
                tableBucketARN=table_bucket_arn
            )
            return {
                "table_bucket_arn": table_bucket_arn,
                "status": "policy_deleted",
            }
        except ClientError as e:
            raise Exception(f"Error deleting table bucket policy: {str(e)}")
