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

"""Email tools for the DataProcessing Agent."""

import os

import boto3
from botocore.exceptions import ClientError
from strands import tool


def create_send_email_tools():
    """Create and return the send_email tool"""

    @tool
    def send_email(to_address: str, subject: str, body: str) -> str:
        """Send a plain text email using Amazon SES via boto3."""
        try:
            # Create a new SES client
            ses_client = boto3.client(
                "ses", region_name=os.getenv("AWS_REGION", "us-east-1")
            )

            # Format the text body for better readability
            formatted_body = body.strip()
            formatted_body = formatted_body.replace("\n\n\n", "\n\n")
            formatted_body = formatted_body.replace("\n", "\n\n")

            # Prepare the email message
            message = {
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": formatted_body}},
            }

            # Send the email
            response = ses_client.send_email(
                Source=os.getenv("SENDER_EMAIL_ADDRESS"),
                Destination={"ToAddresses": [to_address]},
                Message=message,
                ReplyToAddresses=[
                    os.getenv(
                        "REPLY_TO_EMAIL_ADDRESSES",
                        os.getenv("SENDER_EMAIL_ADDRESS"),
                    )
                ],
            )

            return f"✅ Email sent successfully to {to_address}! Message ID: {response['MessageId']}"

        except Exception as e:
            return f"❌ Error sending email: {str(e)}"

    return [send_email]
