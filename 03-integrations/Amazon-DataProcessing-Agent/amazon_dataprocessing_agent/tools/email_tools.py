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

import json
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError


class EmailTools:
    """Tools for sending emails via Amazon SES"""

    def __init__(self, region_name: str = "us-east-1"):
        """Initialize SES client"""
        self.ses_client = boto3.client("ses", region_name=region_name)
        self.region_name = region_name

    def send_simple_email(
        self,
        source: str,
        destination: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a simple email using SES"""
        try:
            # Prepare the email body
            body = {"Text": {"Data": body_text, "Charset": "UTF-8"}}

            if body_html:
                body["Html"] = {"Data": body_html, "Charset": "UTF-8"}

            response = self.ses_client.send_email(
                Source=source,
                Destination={"ToAddresses": [destination]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": body,
                },
            )

            return {
                "message_id": response["MessageId"],
                "source": source,
                "destination": destination,
                "subject": subject,
                "status": "sent",
            }
        except ClientError as e:
            raise Exception(f"Error sending email: {str(e)}")

    def send_bulk_email(
        self,
        source: str,
        destinations: List[str],
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send bulk emails using SES"""
        try:
            # Prepare the email body
            body = {"Text": {"Data": body_text, "Charset": "UTF-8"}}

            if body_html:
                body["Html"] = {"Data": body_html, "Charset": "UTF-8"}

            response = self.ses_client.send_email(
                Source=source,
                Destination={"ToAddresses": destinations},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": body,
                },
            )

            return {
                "message_id": response["MessageId"],
                "source": source,
                "destinations": destinations,
                "destination_count": len(destinations),
                "subject": subject,
                "status": "sent",
            }
        except ClientError as e:
            raise Exception(f"Error sending bulk email: {str(e)}")

    def send_templated_email(
        self,
        source: str,
        destination: str,
        template_name: str,
        template_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Send a templated email using SES"""
        try:
            response = self.ses_client.send_templated_email(
                Source=source,
                Destination={"ToAddresses": [destination]},
                Template=template_name,
                TemplateData=json.dumps(template_data),
            )

            return {
                "message_id": response["MessageId"],
                "source": source,
                "destination": destination,
                "template_name": template_name,
                "status": "sent",
            }
        except ClientError as e:
            raise Exception(f"Error sending templated email: {str(e)}")

    def create_email_template(
        self,
        template_name: str,
        subject: str,
        html_part: Optional[str] = None,
        text_part: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create an email template in SES"""
        try:
            template = {
                "TemplateName": template_name,
                "SubjectPart": subject,
            }

            if html_part:
                template["HtmlPart"] = html_part
            if text_part:
                template["TextPart"] = text_part

            self.ses_client.create_template(Template=template)

            return {
                "template_name": template_name,
                "subject": subject,
                "status": "created",
            }
        except ClientError as e:
            raise Exception(f"Error creating email template: {str(e)}")

    def update_email_template(
        self,
        template_name: str,
        subject: str,
        html_part: Optional[str] = None,
        text_part: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an existing email template in SES"""
        try:
            template = {
                "TemplateName": template_name,
                "SubjectPart": subject,
            }

            if html_part:
                template["HtmlPart"] = html_part
            if text_part:
                template["TextPart"] = text_part

            self.ses_client.update_template(Template=template)

            return {
                "template_name": template_name,
                "subject": subject,
                "status": "updated",
            }
        except ClientError as e:
            raise Exception(f"Error updating email template: {str(e)}")

    def delete_email_template(self, template_name: str) -> Dict[str, Any]:
        """Delete an email template from SES"""
        try:
            self.ses_client.delete_template(TemplateName=template_name)
            return {
                "template_name": template_name,
                "status": "deleted",
            }
        except ClientError as e:
            raise Exception(f"Error deleting email template: {str(e)}")

    def list_email_templates(self) -> List[Dict[str, Any]]:
        """List all email templates in SES"""
        try:
            response = self.ses_client.list_templates()
            return [
                {
                    "name": template["Name"],
                    "created_timestamp": template["CreatedTimestamp"].isoformat(),
                }
                for template in response.get("TemplatesMetadata", [])
            ]
        except ClientError as e:
            raise Exception(f"Error listing email templates: {str(e)}")

    def get_email_template(self, template_name: str) -> Dict[str, Any]:
        """Get details of a specific email template"""
        try:
            response = self.ses_client.get_template(TemplateName=template_name)
            template = response["Template"]
            return {
                "name": template["TemplateName"],
                "subject": template["SubjectPart"],
                "html_part": template.get("HtmlPart"),
                "text_part": template.get("TextPart"),
            }
        except ClientError as e:
            raise Exception(f"Error getting email template: {str(e)}")

    def verify_email_identity(self, email_address: str) -> Dict[str, Any]:
        """Verify an email address for use with SES"""
        try:
            self.ses_client.verify_email_identity(EmailAddress=email_address)
            return {
                "email_address": email_address,
                "status": "verification_sent",
                "message": "Verification email sent. Please check your inbox and click the verification link.",
            }
        except ClientError as e:
            raise Exception(f"Error verifying email identity: {str(e)}")

    def list_verified_email_addresses(self) -> List[str]:
        """List all verified email addresses"""
        try:
            response = self.ses_client.list_verified_email_addresses()
            return response.get("VerifiedEmailAddresses", [])
        except ClientError as e:
            raise Exception(f"Error listing verified email addresses: {str(e)}")

    def delete_verified_email_address(self, email_address: str) -> Dict[str, Any]:
        """Delete a verified email address"""
        try:
            self.ses_client.delete_verified_email_address(EmailAddress=email_address)
            return {
                "email_address": email_address,
                "status": "deleted",
            }
        except ClientError as e:
            raise Exception(f"Error deleting verified email address: {str(e)}")

    def get_send_quota(self) -> Dict[str, Any]:
        """Get the current send quota for SES"""
        try:
            response = self.ses_client.get_send_quota()
            return {
                "max_24_hour_send": response["Max24HourSend"],
                "max_send_rate": response["MaxSendRate"],
                "sent_last_24_hours": response["SentLast24Hours"],
            }
        except ClientError as e:
            raise Exception(f"Error getting send quota: {str(e)}")

    def get_send_statistics(self) -> List[Dict[str, Any]]:
        """Get send statistics for SES"""
        try:
            response = self.ses_client.get_send_statistics()
            return [
                {
                    "timestamp": stat["Timestamp"].isoformat(),
                    "delivery_attempts": stat["DeliveryAttempts"],
                    "bounces": stat["Bounces"],
                    "complaints": stat["Complaints"],
                    "rejects": stat["Rejects"],
                }
                for stat in response.get("SendDataPoints", [])
            ]
        except ClientError as e:
            raise Exception(f"Error getting send statistics: {str(e)}")

    def send_data_processing_notification(
        self,
        source: str,
        destination: str,
        job_name: str,
        job_status: str,
        job_details: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Send a data processing job notification email"""
        try:
            subject = f"Data Processing Job Update: {job_name} - {job_status}"

            # Create HTML body
            html_body = f"""
            <html>
            <head></head>
            <body>
                <h2>Data Processing Job Notification</h2>
                <p><strong>Job Name:</strong> {job_name}</p>
                <p><strong>Status:</strong> {job_status}</p>
                <p><strong>Details:</strong></p>
                <ul>
            """

            for key, value in job_details.items():
                html_body += f"<li><strong>{key}:</strong> {value}</li>"

            html_body += """
                </ul>
                <p>This is an automated notification from the Amazon Data Processing Agent.</p>
            </body>
            </html>
            """

            # Create text body
            text_body = f"""
Data Processing Job Notification

Job Name: {job_name}
Status: {job_status}

Details:
"""
            for key, value in job_details.items():
                text_body += f"- {key}: {value}\n"

            text_body += "\nThis is an automated notification from the Amazon Data Processing Agent."

            return self.send_simple_email(
                source=source,
                destination=destination,
                subject=subject,
                body_text=text_body,
                body_html=html_body,
            )
        except Exception as e:
            raise Exception(f"Error sending data processing notification: {str(e)}")
