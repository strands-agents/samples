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

"""S3 tools for the DataProcessing Agent."""

from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError


class S3Tools:
    """Tools for interacting with Amazon S3"""

    def __init__(self, region_name: str = "us-east-1"):
        """Initialize S3 client"""
        self.s3_client = boto3.client("s3", region_name=region_name)
        self.region_name = region_name

    def list_buckets(self) -> List[Dict[str, Any]]:
        """List all S3 buckets"""
        try:
            response = self.s3_client.list_buckets()
            return [
                {
                    "name": bucket["Name"],
                    "creation_date": bucket["CreationDate"].isoformat(),
                }
                for bucket in response.get("Buckets", [])
            ]
        except ClientError as e:
            raise Exception(f"Error listing buckets: {str(e)}")

    def list_objects(
        self, bucket_name: str, prefix: str = "", max_keys: int = 1000
    ) -> List[Dict[str, Any]]:
        """List objects in an S3 bucket"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name, Prefix=prefix, MaxKeys=max_keys
            )
            return [
                {
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat(),
                    "etag": obj["ETag"],
                }
                for obj in response.get("Contents", [])
            ]
        except ClientError as e:
            raise Exception(f"Error listing objects in bucket {bucket_name}: {str(e)}")

    def upload_file(
        self, file_path: str, bucket_name: str, object_key: str
    ) -> Dict[str, Any]:
        """Upload a file to S3"""
        try:
            self.s3_client.upload_file(file_path, bucket_name, object_key)
            return {
                "bucket": bucket_name,
                "key": object_key,
                "status": "uploaded",
                "s3_uri": f"s3://{bucket_name}/{object_key}",
            }
        except ClientError as e:
            raise Exception(f"Error uploading file to S3: {str(e)}")

    def download_file(
        self, bucket_name: str, object_key: str, file_path: str
    ) -> Dict[str, Any]:
        """Download a file from S3"""
        try:
            self.s3_client.download_file(bucket_name, object_key, file_path)
            return {
                "bucket": bucket_name,
                "key": object_key,
                "local_path": file_path,
                "status": "downloaded",
            }
        except ClientError as e:
            raise Exception(f"Error downloading file from S3: {str(e)}")

    def delete_object(self, bucket_name: str, object_key: str) -> Dict[str, Any]:
        """Delete an object from S3"""
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_key)
            return {
                "bucket": bucket_name,
                "key": object_key,
                "status": "deleted",
            }
        except ClientError as e:
            raise Exception(f"Error deleting object from S3: {str(e)}")

    def get_bucket_location(self, bucket_name: str) -> str:
        """Get the region of an S3 bucket"""
        try:
            response = self.s3_client.get_bucket_location(Bucket=bucket_name)
            location = response.get("LocationConstraint")
            return location if location else "us-east-1"
        except ClientError as e:
            raise Exception(f"Error getting bucket location: {str(e)}")

    def create_presigned_url(
        self, bucket_name: str, object_key: str, expiration: int = 3600
    ) -> str:
        """Generate a presigned URL for an S3 object"""
        try:
            response = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": object_key},
                ExpiresIn=expiration,
            )
            return response
        except ClientError as e:
            raise Exception(f"Error generating presigned URL: {str(e)}")

    def get_object_metadata(self, bucket_name: str, object_key: str) -> Dict[str, Any]:
        """Get metadata for an S3 object"""
        try:
            response = self.s3_client.head_object(Bucket=bucket_name, Key=object_key)
            return {
                "content_length": response.get("ContentLength"),
                "content_type": response.get("ContentType"),
                "last_modified": (
                    response.get("LastModified").isoformat()
                    if response.get("LastModified")
                    else None
                ),
                "etag": response.get("ETag"),
                "metadata": response.get("Metadata", {}),
            }
        except ClientError as e:
            raise Exception(f"Error getting object metadata: {str(e)}")
