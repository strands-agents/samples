import json
import boto3
import logging
import time
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger()


class WhatsappMessage:
    def __init__(
        self,
        meta_phone_number: Dict,
        message: Dict,
        metadata: Optional[Dict] = None,
        meta_api_version: str = "v20.0",
    ) -> None:
        if metadata is None:
            metadata = {}
        self.meta_phone_number = meta_phone_number
        self.phone_number_arn = meta_phone_number.get("arn", "")
        self.meta_phone_number_id = meta_phone_number.get("metaPhoneNumberId", "")
        self.phone_number_id = self.phone_number_arn.split(":")[-1].replace("/", "-")
        self.message = message
        self.metadata = metadata
        self.timestamp = message.get("timestamp", "")
        self.phone_number = message.get("from", "")
        self.meta_api_version = meta_api_version
        self.message_id = message.get("id", "")
    
    def get_text(self) -> str:
        """Retrieve the text body from the message."""
        return self.message.get("text", {}).get("body", "")
    
    def build_whatsapp_row(self, phone_number, messages, role, meta_phone_number_id, 
                           id, phone_number_id, timestamp, system_prompt):
        try:
            current_day = datetime.now().strftime("%Y/%m/%d")
            return {
                    "phone_number": phone_number,
                    "session_time": int(time.time()),
                    "day": current_day,
                    "meta_phone_number_id": meta_phone_number_id,
                    "id": id,
                    "phone_number_id": phone_number_id,
                    "timestamp": timestamp,
                    "messages": messages,
                    "system_prompt": system_prompt
            }
        except Exception as e:
            logger.error(f"Error building WhatsApp row: {str(e)}")
            raise


class WhatsappService:
    def __init__(self, sns_message: Dict, client: Optional[boto3.client] = None) -> None:
        self.context = sns_message.get("context", {})
        self.meta_phone_number_ids = self.context.get("MetaPhoneNumberIds", [])
        self.meta_waba_ids = self.context.get("MetaWabaIds", [])
        self.webhook_entry = json.loads(sns_message.get("whatsAppWebhookEntry", "{}"))
        self.message_timestamp = sns_message.get("message_timestamp", "")
        self.changes = self.webhook_entry.get("changes", [])
        self.messages = []
        self.client = client if client else boto3.client("socialmessaging")

        for change in self.changes:
            value = change.get("value", {})
            field = change.get("field", "")
            if field == "messages":
                metadata = value.get("metadata", {})
                phone_number_id = metadata.get("phone_number_id", "")
                phone_number = self.get_phone_number_arn(phone_number_id)
                for message in value.get("messages", []):
                    self.messages.append(
                        WhatsappMessage(phone_number, message, metadata)
                    )
            else:
                logger.info(f"Unhandled field: {field}")

    def get_phone_number_arn(self, phone_number_id: str) -> Optional[Dict]:
        """Retrieve the phone number ARN based on the phone number ID."""
        for phone_number in self.meta_phone_number_ids:
            if phone_number.get("metaPhoneNumberId") == phone_number_id:
                return phone_number
        return None

    def text_reply(self, phone_number: str, message_id: str, 
                   phone_number_id: str, text_message: str) -> Dict:
        """Send a text reply via WhatsApp."""
        message_object = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "context": {"message_id": message_id},
            "to": f"+{phone_number}",
            "type": "text",
            "text": {"preview_url": False, "body": text_message},
        }
        
        kwargs = {
            "originationPhoneNumberId": phone_number_id,
            "metaApiVersion": "v20.0",
            "message": bytes(json.dumps(message_object), "utf-8"),
        }
        
        try:
            response = self.client.send_whatsapp_message(**kwargs)
            logger.info(f"Message sent successfully: {response}")
            return response
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise