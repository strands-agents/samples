"""Tool for storing data in Bedrock Knowledge Base asynchronously."""

import json
import logging
import os
import threading
import time
import uuid
from typing import Any

import boto3
from strands import tool

# Set up logging
logger = logging.getLogger(__name__)


def _store_in_kb_background(
    content: str, title: str, kb_id: str, region_name: str
) -> None:
    """Background worker function that performs the actual KB storage.

    This runs in a separate thread and handles all the KB operations.
    Whole validation is done in the main thread before calling this function.

    Args:
        content: The text content to store
        title: The title for the content
        kb_id: The knowledge base ID
        region_name: The AWS region to use
    """
    try:
        # Generate document ID with timestamp for traceability
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        doc_id = f"memory_{timestamp}_{str(uuid.uuid4())[:8]}"

        # Package content with title for better organization
        content_with_metadata = {
            "title": title,
            "action": "store",
            "content": content,
        }

        # Initialize Bedrock agent client
        bedrock_agent_client = boto3.client("bedrock-agent", region_name=region_name)

        # Get the data source ID associated with the knowledge base
        data_sources = bedrock_agent_client.list_data_sources(knowledgeBaseId=kb_id)

        if not data_sources.get("dataSourceSummaries"):
            logger.error(
                f"No data sources found for knowledge base {kb_id}, region {region_name}."
            )
            return

        # Look for a CUSTOM data source type first, as it's required for inline content ingestion
        data_source_id = None
        source_type = None

        for ds in data_sources["dataSourceSummaries"]:
            # Get the data source details to check its type
            ds_detail = bedrock_agent_client.get_data_source(
                knowledgeBaseId=kb_id, dataSourceId=ds["dataSourceId"]
            )

            # Check if this is a CUSTOM type data source
            if ds_detail["dataSource"]["dataSourceConfiguration"]["type"] == "CUSTOM":
                data_source_id = ds["dataSourceId"]
                source_type = "CUSTOM"
                logger.debug(f"Found CUSTOM data source: {data_source_id}")
                break

        # If no CUSTOM data source found, use the first available one but log a warning
        if not data_source_id and data_sources["dataSourceSummaries"]:
            data_source_id = data_sources["dataSourceSummaries"][0]["dataSourceId"]
            ds_detail = bedrock_agent_client.get_data_source(
                knowledgeBaseId=kb_id, dataSourceId=data_source_id
            )
            source_type = ds_detail["dataSource"]["dataSourceConfiguration"]["type"]
            logger.debug(
                f"No CUSTOM data source found. Using {source_type} data source: {data_source_id}"
            )

        if not data_source_id:
            logger.error(f"No suitable data source found for knowledge base {kb_id}.")
            return

        # Prepare document for ingestion based on the data source type
        if source_type == "CUSTOM":
            ingest_request = {
                "knowledgeBaseId": kb_id,
                "dataSourceId": data_source_id,
                "documents": [
                    {
                        "content": {
                            "dataSourceType": "CUSTOM",
                            "custom": {
                                "customDocumentIdentifier": {"id": doc_id},
                                "inlineContent": {
                                    "textContent": {
                                        "data": json.dumps(content_with_metadata)
                                    },
                                    "type": "TEXT",
                                },
                                "sourceType": "IN_LINE",
                            },
                        }
                    }
                ],
            }
        elif source_type == "S3":
            # S3 source types need a different ingestion approach
            logger.error(
                "S3 data source type is not supported for direct ingestion with this tool."
            )
            return
        else:
            logger.error(f"Unsupported data source type: {source_type}")
            return

        # Ingest document into knowledge base
        _ = bedrock_agent_client.ingest_knowledge_base_documents(**ingest_request)

        # Log success
        logger.info(
            f"Successfully ingested document into knowledge base {kb_id}: {doc_id}"
        )

    except Exception as e:
        logger.error(f"Error ingesting into knowledge base: {e!s}")


@tool
def store_in_kb(
    content: str, title: str | None = None, knowledge_base_id: str | None = None
) -> dict[str, Any]:
    """Store content in a Bedrock Knowledge Base using real-time ingestion.

    This version runs asynchronously in a background thread and returns immediately.

    Args:
        content: The text content to store in the knowledge base.
        title: Optional title for the content. If not provided, a timestamp will be used.
        knowledge_base_id: Optional knowledge base ID. If not provided, will use the STRANDS_KNOWLEDGE_BASE_ID env.

    Returns:
        A dictionary containing the result of the operation.
    """
    # All validation done in main thread before spawning background thread

    # Validate content first
    if not content or not content.strip():
        return {"status": "error", "content": [{"text": "❌ Content cannot be empty"}]}

    # Resolve and validate knowledge base ID early (addresses environment variable race condition)
    kb_id = knowledge_base_id or os.getenv("STRANDS_KNOWLEDGE_BASE_ID")
    if not kb_id:
        return {
            "status": "error",
            "content": [
                {
                    "text": "❌ No knowledge base ID provided or found in environment variables STRANDS_KNOWLEDGE_BASE_ID"
                }
            ],
        }

    region_name = os.getenv("AWS_REGION", "us-west-2")

    doc_title = title or f"Strands Memory {time.strftime('%Y%m%d_%H%M%S')}"

    thread = threading.Thread(
        target=_store_in_kb_background,
        args=(content, doc_title, kb_id, region_name),
        daemon=True,
    )
    thread.start()

    # Return immediately with status
    return {
        "status": "success",
        "content": [
            {"text": "✅ Started background task to store content in knowledge base:"},
            {"text": f"📝 Title: {doc_title}"},
            {"text": f"🗄️ Knowledge Base ID: {kb_id}"},
            {"text": "⏱️ Processing in background..."},
        ],
    }
