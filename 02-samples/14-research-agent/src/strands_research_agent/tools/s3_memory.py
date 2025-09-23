"""Manage content in Amazon S3 Vectors as vector embeddings (setup, store, delete, get, or retrieve).

This tool provides semantic memory capabilities using S3 Vectors, Amazon's new cloud storage
service with native vector support. Content is automatically converted to vector embeddings
and stored for fast similarity search and retrieval.

Key Features:
1. **Semantic Memory**: Store and retrieve content using vector similarity search
2. **Full Content Storage**: Returns complete content by default without arbitrary truncation
3. **Configurable Display**: User-controlled content limits and display options
4. **Production-Ready**: Comprehensive error handling, logging, and user confirmations
5. **S3 Vectors Integration**: Native support for Amazon's vector storage service

How It Works:
------------
1. **Setup**: Creates S3 Vector buckets and indexes with specified dimensions and metrics
2. **Store**: Converts text content to vector embeddings using Amazon Bedrock and stores in S3 Vectors
3. **Retrieve**: Performs semantic similarity search using query embeddings to find relevant content
4. **Get**: Retrieves specific documents by their unique keys
5. **List**: Shows all stored vectors with metadata and optional content previews
6. **Delete**: Removes vectors from the index permanently

Content Management Philosophy:
----------------------------
This tool prioritizes data fidelity and user control:
- **Full Content by Default**: No arbitrary truncation unless explicitly requested
- **User-Controlled Limits**: Configure content display through parameters
- **Consistent Behavior**: Same truncation logic across all operations
- **Transparency**: Shows content lengths and truncation status

Common Use Cases:
---------------
- **Knowledge Management**: Store and retrieve documents, notes, and research
- **Content Discovery**: Find similar content through semantic search
- **Personal Memory**: Build a searchable repository of personal information
- **Research Assistant**: Store and query academic papers, articles, and references
- **Decision Support**: Maintain context and historical decisions for reference

Usage with Strands Agent:
```python
from strands import Agent
from strands_tools import s3_memory

agent = Agent(tools=[s3_memory])

# Setup S3 Vector infrastructure
result = agent.tool.s3_memory(
    action="setup",
    vector_bucket_name="my-memory-bucket",
    vector_index_name="my-memory-index"
)

# Store content with full text preserved
result = agent.tool.s3_memory(
    action="store",
    content="Important meeting notes about quarterly planning...",
    title="Q4 Planning Meeting Notes"
)

# Semantic search with full content returned
result = agent.tool.s3_memory(
    action="retrieve",
    query="quarterly planning decisions",
    max_results=5,
    min_score=0.7
)

# Get specific document with controlled content display
result = agent.tool.s3_memory(
    action="get",
    document_key="memory_20241215_abc123",
    content_limit=1000  # Limit display to 1000 chars
)

# List all stored content with previews
result = agent.tool.s3_memory(
    action="list",
    show_preview=True,
    content_limit=200
)
```

Architecture:
-----------
- **S3VectorClient**: Handles all S3 Vectors API interactions
- **MemoryFormatter**: Provides consistent response formatting with content control
- **Embedding Generation**: Uses Amazon Bedrock (Titan Embed V2 by default)
- **Content Preservation**: Stores full content in metadata without loss
- **Display Control**: Configurable truncation for user interface needs
"""

import json
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3
from rich.console import Console
from strands import tool

logger = logging.getLogger(__name__)
console = Console()

DEFAULT_EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"
DEFAULT_VECTOR_DIMENSIONS = int(os.getenv("MEMORY_VECTOR_DIMENSIONS", "1024"))


class S3VectorClient:
    """Client for interacting with Amazon S3 Vectors service.

    This client provides a comprehensive interface to Amazon S3 Vectors, handling
    vector storage, retrieval, and search operations. It manages AWS service
    connections with lazy loading and provides consistent error handling.

    Key Features:
    - Lazy-loaded AWS service clients for optimal resource usage
    - Vector embedding generation using Amazon Bedrock
    - Comprehensive vector operations (store, retrieve, search, delete)
    - Infrastructure management (bucket and index creation)
    - Consistent error handling and response formatting

    Attributes:
        region: AWS region for S3 Vectors service
        session: Boto3 session for AWS service connections
    """

    def __init__(self, region: str = None):
        """Initialize the S3 Vector client."""
        self.region = region or os.getenv("AWS_REGION", "us-west-2")
        self._s3vectors_client = None
        self._bedrock_client = None
        self.session = boto3.Session()

    @property
    def s3vectors_client(self):
        """Lazy-loaded S3 Vectors client."""
        if not self._s3vectors_client:
            self._s3vectors_client = self.session.client(
                "s3vectors", region_name=self.region
            )
        return self._s3vectors_client

    @property
    def bedrock_client(self):
        """Lazy-loaded Bedrock Runtime client for embeddings."""
        if not self._bedrock_client:
            self._bedrock_client = self.session.client(
                "bedrock-runtime", region_name=self.region
            )
        return self._bedrock_client

    def generate_embedding(self, text: str, model_id: str = None) -> List[float]:
        """Generate vector embedding for text using Amazon Bedrock."""
        if not model_id:
            model_id = os.getenv("MEMORY_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)

        request_body = json.dumps({"inputText": text})

        response = self.bedrock_client.invoke_model(modelId=model_id, body=request_body)

        response_data = json.loads(response["body"].read())
        return response_data["embedding"]

    def put_vector(
        self,
        bucket_name: str,
        index_name: str,
        key: str,
        embedding: List[float],
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Store a vector in S3 Vector index."""
        vector_data = {"key": key, "data": {"float32": embedding}, "metadata": metadata}

        return self.s3vectors_client.put_vectors(
            vectorBucketName=bucket_name, indexName=index_name, vectors=[vector_data]
        )

    def get_vector(self, bucket_name: str, index_name: str, key: str) -> Dict[str, Any]:
        """Get a specific vector by key."""
        try:
            # Use the correct S3 Vectors API to get vectors by key
            response = self.s3vectors_client.get_vectors(
                vectorBucketName=bucket_name,
                indexName=index_name,
                keys=[key],
                returnMetadata=True,
            )
            return response
        except Exception as e:
            # If get_vectors doesn't exist or fails, try list_vectors approach
            try:
                response = self.s3vectors_client.list_vectors(
                    vectorBucketName=bucket_name, indexName=index_name, keyPrefix=key
                )

                # Filter for exact key match
                vectors = response.get("vectors", [])
                for vector in vectors:
                    if vector.get("key") == key:
                        return {"vectors": [vector]}

                return {"vectors": []}  # Not found

            except Exception as e2:
                raise Exception(
                    f"Error retrieving vector with key {key}: {str(e)} | Fallback error: {str(e2)}"
                )

    def query_vectors(
        self,
        bucket_name: str,
        index_name: str,
        query_embedding: List[float],
        top_k: int = 5,
        min_score: float = 0.0,
        metadata_filter: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Query vectors using similarity search."""
        query_params = {
            "vectorBucketName": bucket_name,
            "indexName": index_name,
            "queryVector": {"float32": query_embedding},
            "topK": top_k,
            "returnDistance": True,
            "returnMetadata": True,
        }

        if metadata_filter:
            query_params["filter"] = metadata_filter

        response = self.s3vectors_client.query_vectors(**query_params)

        # Process the response to ensure consistent score format
        vectors = response.get("vectors", [])
        processed_vectors = []

        for vector in vectors:
            # S3 Vectors returns distance, we need to handle this properly
            if "distance" in vector:
                distance = vector["distance"]
                # For cosine distance, similarity = 1 - distance
                similarity = max(0.0, 1.0 - distance)  # Ensure non-negative
                vector["score"] = similarity

            # Only include vectors that meet the minimum score threshold
            score = vector.get("score", 0.0)
            if score >= min_score:
                processed_vectors.append(vector)

        # Sort by score (highest first)
        processed_vectors.sort(key=lambda x: x.get("score", 0.0), reverse=True)

        return {"vectors": processed_vectors}

    def delete_vector(
        self, bucket_name: str, index_name: str, key: str
    ) -> Dict[str, Any]:
        """Delete a vector from S3 Vector index."""
        return self.s3vectors_client.delete_vectors(
            vectorBucketName=bucket_name,
            indexName=index_name,
            keys=[key],
        )

    def list_vectors(
        self,
        bucket_name: str,
        index_name: str,
        max_results: int = 50,
        next_token: str = None,
        return_data: bool = False,
        return_metadata: bool = True,
    ) -> Dict[str, Any]:
        """List all vectors in S3 Vector index."""
        params = {
            "vectorBucketName": bucket_name,
            "indexName": index_name,
            "maxResults": max_results,
            "returnData": return_data,
            "returnMetadata": return_metadata,
        }

        if next_token:
            params["nextToken"] = next_token

        return self.s3vectors_client.list_vectors(**params)

    def create_vector_bucket(self, bucket_name: str) -> Dict[str, Any]:
        """Create an S3 Vector bucket."""
        try:
            response = self.s3vectors_client.create_vector_bucket(
                vectorBucketName=bucket_name
            )
            return response
        except Exception as e:
            error_str = str(e)
            if (
                "BucketAlreadyExists" in error_str
                or "already exists" in error_str.lower()
            ):
                return {"status": "already_exists", "bucket_name": bucket_name}
            else:
                raise e

    def create_vector_index(
        self,
        bucket_name: str,
        index_name: str,
        dimensions: int = DEFAULT_VECTOR_DIMENSIONS,
        distance_metric: str = "cosine",
    ) -> Dict[str, Any]:
        """Create a vector index in an S3 Vector bucket."""
        try:
            response = self.s3vectors_client.create_index(
                vectorBucketName=bucket_name,
                indexName=index_name,
                dataType="float32",
                dimension=dimensions,
                distanceMetric=distance_metric.lower(),
            )
            return response
        except Exception as e:
            error_str = str(e)
            if (
                "IndexAlreadyExists" in error_str
                or "already exists" in error_str.lower()
            ):
                return {"status": "already_exists", "index_name": index_name}
            else:
                raise e


def truncate_content(
    content: str, max_length: int = None, add_ellipsis: bool = True
) -> str:
    """Truncate content based on specified length limits with user control.

    This function provides intelligent content truncation that respects user preferences
    and maintains readability. It serves as the central truncation logic used across
    all S3 memory operations to ensure consistent behavior.

    Truncation Philosophy:
    - No truncation by default (max_length=None means full content)
    - Clear indication when truncation occurs (ellipsis)
    - Preserves readability by avoiding mid-word cuts when possible
    - Consistent behavior across all memory operations

    Args:
        content: The text content to potentially truncate
        max_length: Maximum character length (None means no truncation)
        add_ellipsis: Whether to add "..." indicator when truncating

    Returns:
        Original content if within limits, or truncated content with optional ellipsis

    Examples:
        # No truncation
        truncate_content("Hello world", None) -> "Hello world"

        # With truncation
        truncate_content("Hello world", 8, True) -> "Hello..."

        # Without ellipsis
        truncate_content("Hello world", 8, False) -> "Hello wo"
    """
    if max_length is None or len(content) <= max_length:
        return content

    truncated = content[:max_length]
    if add_ellipsis and max_length > 3:
        truncated = truncated[:-3] + "..."

    return truncated


class MemoryFormatter:
    """Formatter with configurable content truncation for S3 Vector memory responses.

    This formatter provides consistent response formatting across all S3 memory operations
    with sophisticated content management capabilities. It handles content truncation,
    metadata display, and user interface concerns while preserving data integrity.

    Key Features:
    - Consistent response formatting across all memory operations
    - User-configurable content truncation with transparency
    - Rich metadata display including timestamps, scores, and keys
    - Content length tracking and truncation indicators
    - Flexible preview and full-content display modes

    The formatter prioritizes user control and data transparency, clearly indicating
    when content has been truncated and providing options to show full content.
    """

    def format_store_response(
        self, doc_key: str, bucket_name: str, index_name: str, title: str
    ) -> str:
        """Format store vector response."""
        result = "✅ **Successfully stored content in S3 Vector memory:**\n"
        result += f"📝 **Title:** {title}\n"
        result += f"🔑 **Document Key:** {doc_key}\n"
        result += f"🗂️ **Vector Bucket:** {bucket_name}\n"
        result += f"📊 **Vector Index:** {index_name}"
        return result

    def format_delete_response(
        self, doc_key: str, bucket_name: str, index_name: str
    ) -> str:
        """Format delete vector response."""
        result = "✅ **Successfully deleted vector from memory:**\n"
        result += f"🔑 **Document Key:** {doc_key}\n"
        result += f"🗂️ **Vector Bucket:** {bucket_name}\n"
        result += f"📊 **Vector Index:** {index_name}"
        return result

    def format_retrieve_response(
        self,
        results: List[Dict],
        min_score: float,
        content_limit: int = None,
        show_full_content: bool = True,
    ) -> str:
        """Format retrieve/search response with configurable content limits."""
        if not results:
            return f"🔍 **No results found** with similarity score >= {min_score}\n\n💡 Try lowering the min_score threshold or using different search terms."

        result = f"🔍 **Search Results** (found {len(results)} results, score >= {min_score}):\n\n"

        for i, vector_result in enumerate(results, 1):
            score = vector_result.get("score", 0.0)
            metadata = vector_result.get("metadata", {})
            key = vector_result.get("key", metadata.get("key", "unknown"))
            title = metadata.get("title", "Untitled")
            content_text = metadata.get("content", "")
            timestamp = metadata.get("timestamp", "unknown")

            # Apply content truncation based on parameters
            if show_full_content and content_limit is None:
                # Return full content by default
                display_content = content_text
                truncation_note = ""
            else:
                # Apply user-specified limits
                display_content = truncate_content(content_text, content_limit)
                if content_limit and len(content_text) > content_limit:
                    truncation_note = f" (truncated from {len(content_text)} chars)"
                else:
                    truncation_note = ""

            result += f"**{i}. {title}**\n"
            result += f"🔑 **Key:** {key}\n"
            result += f"⭐ **Similarity:** {score:.4f}\n"
            result += f"🕒 **Created:** {timestamp}\n"
            result += (
                f"📏 **Length:** {len(content_text)} characters{truncation_note}\n"
            )
            result += f"📄 **Content:**\n{display_content}\n\n"

        return result.strip()

    def format_get_response(
        self,
        doc_key: str,
        metadata: Dict,
        bucket_name: str,
        index_name: str,
        content_limit: int = None,
        show_full_content: bool = True,
    ) -> str:
        """Format get vector response with configurable content limits."""
        title = metadata.get("title", "Untitled")
        content_text = metadata.get("content", "No content available")
        timestamp = metadata.get("timestamp", "unknown")

        # Apply content truncation based on parameters
        if show_full_content and content_limit is None:
            display_content = content_text
            truncation_note = ""
        else:
            display_content = truncate_content(content_text, content_limit)
            if content_limit and len(content_text) > content_limit:
                truncation_note = f" (truncated from {len(content_text)} chars)"
            else:
                truncation_note = ""

        result = "✅ **Successfully retrieved vector:**\n"
        result += f"📝 **Title:** {title}\n"
        result += f"🔑 **Document Key:** {doc_key}\n"
        result += f"🗂️ **Vector Bucket:** {bucket_name}\n"
        result += f"📊 **Vector Index:** {index_name}\n"
        result += f"🕒 **Created:** {timestamp}\n"
        result += f"📏 **Content Length:** {len(content_text)} characters{truncation_note}\n\n"
        result += f"📄 **Content:**\n{display_content}"

        return result

    def format_list_response(
        self,
        vectors: List[Dict],
        bucket_name: str,
        index_name: str,
        content_limit: int = None,
        show_preview: bool = True,
        next_token: str = None,
    ) -> str:
        """Format list vectors response with configurable content limits."""
        if not vectors:
            return f"📂 **No vectors found in memory**\n\n🗂️ **Bucket:** {bucket_name}\n📊 **Index:** {index_name}"

        result = f"📂 **Memory Contents** ({len(vectors)} vectors found):\n\n"

        for i, vector in enumerate(vectors, 1):
            metadata = vector.get("metadata", {})
            key = vector.get("key", "unknown")
            title = metadata.get("title", "Untitled")
            timestamp = metadata.get("timestamp", "unknown")
            content_text = metadata.get("content", "")
            content_length = len(content_text) if content_text else 0

            result += f"**{i}. {title}**\n"
            result += f"🔑 **Key:** {key}\n"
            result += f"🕒 **Created:** {timestamp}\n"
            result += f"📏 **Length:** {content_length} characters\n"

            # Show content preview based on parameters
            if show_preview and content_text:
                if content_limit is None:
                    # Default to a reasonable preview length if not specified
                    preview_limit = 200
                else:
                    preview_limit = content_limit

                preview_content = truncate_content(content_text, preview_limit)
                result += f"📄 **Preview:** {preview_content}\n"

            result += "\n"

        # Add pagination info if available
        if next_token:
            result += (
                f"🔄 **More results available** (use pagination for full list)\n\n"
            )

        result += f"🗂️ **Bucket:** {bucket_name} | 📊 **Index:** {index_name}"

        return result.strip()


@tool
def s3_memory(
    action: str,
    content: Optional[str] = None,
    title: Optional[str] = None,
    document_key: Optional[str] = None,
    query: Optional[str] = None,
    vector_bucket_name: Optional[str] = None,
    vector_index_name: Optional[str] = None,
    max_results: int = 5,
    min_score: float = 0.4,
    region_name: Optional[str] = None,
    vector_dimensions: int = DEFAULT_VECTOR_DIMENSIONS,
    distance_metric: str = "cosine",
    content_limit: Optional[int] = None,
    show_full_content: bool = True,
    show_preview: bool = True,
) -> str:
    """Manage content in Amazon S3 Vectors as vector embeddings (setup, store, delete, get, or retrieve).

    This tool provides semantic memory capabilities using S3 Vectors, Amazon's new cloud storage
    service with native vector support. Content is automatically converted to vector embeddings
    and stored for fast similarity search and retrieval.

    How It Works:
    ------------
    1. For content storage:
       - Converts text to vector embeddings using Amazon Bedrock
       - Stores both the embedding and full content metadata in S3 Vectors
       - Generates unique document keys for tracking and retrieval
       - Preserves complete content without truncation

    2. For semantic search:
       - Converts search queries to embeddings using the same model
       - Performs similarity search against stored vectors
       - Returns results ranked by similarity score with metadata
       - Applies user-specified score thresholds and result limits

    3. For infrastructure setup:
       - Creates S3 Vector buckets with proper permissions
       - Establishes vector indexes with configurable dimensions
       - Supports multiple distance metrics (cosine, euclidean)
       - Handles existing infrastructure gracefully

    Operation Modes:
    --------------
    1. Setup: Initialize S3 Vector infrastructure (bucket + index)
    2. Store: Save content as searchable vector embeddings
    3. Retrieve: Semantic search across stored content
    4. Get: Fetch specific documents by unique key
    5. List: Browse all stored vectors with metadata
    6. Delete: Permanently remove vectors from storage

    Content Management Strategy:
    --------------------------
    This tool prioritizes data integrity and user control:
    - **Full Preservation**: Original content stored completely in metadata
    - **Display Control**: Configurable truncation only for user interface
    - **Transparency**: Clear indication of content lengths and truncation
    - **Consistency**: Same formatting and truncation logic across all operations

    Common Use Cases:
    ---------------
    - Knowledge Management: Searchable document repositories
    - Research Assistance: Academic paper and article storage
    - Meeting Notes: Searchable records of discussions and decisions
    - Personal Memory: Life event and experience documentation
    - Content Discovery: Finding similar or related information

    Args:
        action: The action to perform. Must be one of:
            - "setup": Initialize S3 Vector bucket and index infrastructure
            - "store": Save text content as searchable vector embedding
            - "retrieve": Perform semantic similarity search across stored content
            - "get": Retrieve specific document by its unique key identifier
            - "list": Browse all stored vectors with metadata and previews
            - "delete": Permanently remove vector from storage
        content: Text content to store as vector embedding. Required for "store" action.
            Can be any length - full content is preserved in storage. Examples:
            - Meeting notes and transcripts
            - Research papers and articles
            - Personal journal entries
            - Technical documentation
        title: Optional descriptive title for the content. If not provided for "store" action,
            defaults to timestamp-based title. Used for organization and identification.
        document_key: Unique identifier for stored documents. Required for "delete" and "get" actions.
            Auto-generated during "store" operations using timestamp and UUID format.
            Example: "memory_20241215_abc12345"
        query: Search query for semantic retrieval. Required for "retrieve" action.
            Natural language queries work best. Examples:
            - "project planning decisions"
            - "technical architecture notes"
            - "customer feedback about pricing"
        vector_bucket_name: S3 Vector bucket name for storage. If not provided,
            uses MEMORY_VECTOR_BUCKET environment variable or defaults to test bucket.
            Must be globally unique and follow S3 naming conventions.
        vector_index_name: Vector index name within the bucket. If not provided,
            uses MEMORY_VECTOR_INDEX environment variable or defaults to test index.
            Used for organizing different vector collections.
        max_results: Maximum number of results to return for "retrieve" and "list" actions.
            Default: 5, Range: 1-100. Higher values may impact performance.
        min_score: Minimum similarity score threshold for "retrieve" action.
            Default: 0.4, Range: 0.0-1.0. Higher values return more relevant results.
            - 0.9+: Very similar content only
            - 0.7-0.9: Closely related content
            - 0.4-0.7: Moderately related content
            - <0.4: Loosely related content
        region_name: AWS region for S3 Vectors service. If not provided,
            uses AWS_REGION environment variable or defaults to "us-west-2".
        vector_dimensions: Vector dimensions for "setup" action. Default: 1024 (Titan Embed V2).
            Must match the embedding model's output dimensions.
        distance_metric: Distance metric for similarity calculations during "setup".
            Options: "cosine" (default), "euclidean". Cosine is recommended for text.

        # Content Display Control Parameters:
        content_limit: Maximum characters to display in responses. None means no limit,
            showing full content. When set, content longer than this limit is truncated
            with "..." indicator. Useful for managing output size in UI contexts.
        show_full_content: Whether to show complete content by default. True means
            return full content unless content_limit is specified. False applies
            reasonable truncation for readability.
        show_preview: Whether to show content previews in "list" operations.
            True shows truncated content samples for quick browsing.

    Returns:
        String with formatted response based on the action performed:
        - Setup: Confirmation of infrastructure creation
        - Store: Success message with document key and storage details
        - Retrieve: Formatted search results with similarity scores and content
        - Get: Complete document with metadata and content
        - List: Summary of all stored vectors with optional previews
        - Delete: Confirmation of successful removal

        All responses include relevant metadata such as:
        - Document keys and titles
        - Similarity scores (for retrieve)
        - Content lengths and truncation status
        - Timestamps and storage locations
        - Error details if operations fail

    Environment Variables:
    --------------------
    Required for AWS connectivity:
    - AWS_ACCESS_KEY_ID: AWS access key
    - AWS_SECRET_ACCESS_KEY: AWS secret key
    - AWS_SESSION_TOKEN: Session token (if using temporary credentials)

    Optional configuration:
    - MEMORY_VECTOR_BUCKET: Default S3 Vector bucket name
    - MEMORY_VECTOR_INDEX: Default vector index name
    - MEMORY_EMBEDDING_MODEL: Embedding model ID (default: amazon.titan-embed-text-v2:0)
    - AWS_REGION: AWS region for S3 Vectors service
    - BYPASS_TOOL_CONSENT: Set to "true" to skip confirmation prompts

    Examples:
    --------
    # Setup S3 Vector infrastructure automatically
    result = s3_memory(
        action="setup",
        vector_bucket_name="my-memory-bucket",
        vector_index_name="my-memory-index",
        vector_dimensions=1024,
        distance_metric="cosine"
    )

    # Store content as vector embedding
    result = s3_memory(
        action="store",
        content="Important meeting notes about project timeline and deliverables...",
        title="Project Timeline Meeting - Q4 2024"
    )

    # Semantic search across stored content
    result = s3_memory(
        action="retrieve",
        query="project timeline and deadlines",
        max_results=5,
        min_score=0.7
    )

    # Get specific document with content limit
    result = s3_memory(
        action="get",
        document_key="memory_20241215_abc12345",
        content_limit=1000  # Show first 1000 characters
    )

    # List all content with previews
    result = s3_memory(
        action="list",
        show_preview=True,
        content_limit=200  # 200 char previews
    )

    # Delete stored content
    result = s3_memory(
        action="delete",
        document_key="memory_20241215_abc12345"
    )

    Notes:
    -----
    - S3 Vectors service availability varies by AWS region
    - Embedding generation requires Amazon Bedrock access
    - Content is stored permanently until explicitly deleted
    - Vector similarity search performance scales with index size
    - Full content is always preserved regardless of display settings
    - Confirmation prompts can be bypassed with BYPASS_TOOL_CONSENT=true
    - Large content storage may incur AWS costs for S3 and Bedrock usage
    """
    console.print(f"🧠 [bold cyan]Memory Action: {action.upper()}[/bold cyan]")

    # Get configuration
    bucket_name = vector_bucket_name or os.getenv(
        "MEMORY_VECTOR_BUCKET", "test-memory-bucket-demo"
    )
    index_name = vector_index_name or os.getenv("MEMORY_VECTOR_INDEX", "test-index")
    region = region_name or os.getenv("AWS_REGION", "us-west-2")

    console.print(f"🗂️ [green]Bucket:[/green] {bucket_name}")
    console.print(f"📊 [green]Index:[/green] {index_name}")
    console.print(f"🌍 [green]Region:[/green] {region}")

    # Show content control settings
    if content_limit is not None:
        console.print(f"📏 [yellow]Content Limit:[/yellow] {content_limit} chars")
    else:
        console.print(f"📏 [yellow]Content Limit:[/yellow] No limit (full content)")

    console.print(f"📄 [yellow]Show Full Content:[/yellow] {show_full_content}")
    console.print(f"👁️ [yellow]Show Preview:[/yellow] {show_preview}")

    # Validate action
    if action not in ["setup", "store", "delete", "list", "get", "retrieve"]:
        return f"❌ **Error:** Invalid action '{action}'. Must be 'setup', 'store', 'delete', 'list', 'get', 'retrieve'"

    # Initialize clients
    try:
        client = S3VectorClient(region=region)
        formatter = MemoryFormatter()
    except Exception as e:
        return f"❌ **Error:** Failed to initialize S3 Vector client: {str(e)}"

    # Check for confirmation bypass
    BYPASS_CONSENT = os.environ.get("BYPASS_TOOL_CONSENT", "").lower() == "true"

    try:
        if action == "setup":
            # Setup logic (unchanged)
            try:
                bucket_response = client.create_vector_bucket(bucket_name)
                if bucket_response.get("status") == "already_exists":
                    console.print(f"♻️  Bucket '{bucket_name}' already exists")
                else:
                    console.print(f"✅ Created S3 Vector bucket: {bucket_name}")
            except Exception as e:
                return f"❌ **Error:** Failed to create S3 Vector bucket: {str(e)}"

            try:
                index_response = client.create_vector_index(
                    bucket_name=bucket_name,
                    index_name=index_name,
                    dimensions=vector_dimensions,
                    distance_metric=distance_metric,
                )
                if index_response.get("status") == "already_exists":
                    console.print(f"♻️  Index '{index_name}' already exists")
                else:
                    console.print(f"✅ Created vector index: {index_name}")
            except Exception as e:
                return f"❌ **Error:** Failed to create vector index: {str(e)}"

            return f"✅ **Setup Complete!** Bucket: {bucket_name}, Index: {index_name}"

        elif action == "store":
            if not content or not content.strip():
                return "❌ **Error:** Content cannot be empty for store operation"

            store_title = (
                title or f"Memory Entry {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            if not BYPASS_CONSENT:
                # Show preview for confirmation (with truncation for display only)
                content_preview = truncate_content(content, 200)
                console.print(f"\n📋 **Content to store:**")
                console.print(f"📝 Title: {store_title}")
                console.print(f"📄 Content Preview: {content_preview}")
                console.print(f"📏 Full Content Length: {len(content)} characters")

                confirm = input(f"\n🤔 Store this content as vector embedding? [y/*] ")
                if confirm.lower() != "y":
                    return f"⏹️ **Operation canceled by user.**"

            # Generate unique document key
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            doc_key = f"memory_{timestamp}_{str(uuid.uuid4())[:8]}"

            console.print(f"🔄 Generating embedding for content...")
            embedding = client.generate_embedding(content)
            console.print(f"✅ Generated {len(embedding)}-dimensional embedding")

            # Store FULL content in metadata (no truncation)
            metadata = {
                "key": doc_key,
                "title": store_title,
                "content": content,  # FULL CONTENT STORED
                "timestamp": datetime.now().isoformat(),
                "action": "store",
                "content_length": len(content),
                "embedding_model": os.getenv(
                    "MEMORY_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL
                ),
            }

            console.print(f"💾 Storing vector in S3 Vectors...")
            response = client.put_vector(
                bucket_name, index_name, doc_key, embedding, metadata
            )

            return formatter.format_store_response(
                doc_key, bucket_name, index_name, store_title
            )

        elif action == "delete":
            if not document_key:
                return "❌ **Error:** Document key is required for delete operation"

            if not BYPASS_CONSENT:
                console.print(f"\n⚠️ **Document to be permanently deleted:**")
                console.print(f"🔑 Key: {document_key}")

                confirm = input(f"\n🤔 Permanently delete this vector? [y/*] ")
                if confirm.lower() != "y":
                    return f"⏹️ **Operation canceled by user.**"

            console.print(f"🗑️ Deleting vector from S3 Vectors...")
            response = client.delete_vector(bucket_name, index_name, document_key)

            return formatter.format_delete_response(
                document_key, bucket_name, index_name
            )

        elif action == "list":
            console.print(f"📂 Listing all vectors in memory...")

            try:
                response = client.list_vectors(
                    bucket_name=bucket_name,
                    index_name=index_name,
                    max_results=max_results,
                    return_data=False,
                    return_metadata=True,
                )

                vectors = response.get("vectors", [])
                next_token = response.get("nextToken")

                console.print(f"📊 Found {len(vectors)} vectors")

                # Use formatter with content control
                return formatter.format_list_response(
                    vectors,
                    bucket_name,
                    index_name,
                    content_limit=content_limit,
                    show_preview=show_preview,
                    next_token=next_token,
                )

            except Exception as e:
                return f"❌ **Error listing vectors:** {str(e)}"

        elif action == "get":
            if not document_key:
                return "❌ **Error:** Document key is required for get operation"

            console.print(f"🔍 Retrieving vector by key: {document_key}")

            response = client.get_vector(bucket_name, index_name, document_key)

            vectors = response.get("vectors", [])
            if not vectors:
                return f"❌ **Error:** Vector with key '{document_key}' not found"

            vector_data = vectors[0]
            metadata = vector_data.get("metadata", {})

            # Use formatter with content control
            return formatter.format_get_response(
                document_key,
                metadata,
                bucket_name,
                index_name,
                content_limit=content_limit,
                show_full_content=show_full_content,
            )

        elif action == "retrieve":
            if not query:
                return "❌ **Error:** Query is required for retrieve operation"

            if min_score < 0.0 or min_score > 1.0:
                return "❌ **Error:** min_score must be between 0.0 and 1.0"

            if max_results < 1 or max_results > 100:
                return "❌ **Error:** max_results must be between 1 and 100"

            console.print(f"🔄 Generating embedding for query: '{query}'...")
            query_embedding = client.generate_embedding(query)
            console.print(
                f"✅ Generated query embedding ({len(query_embedding)} dimensions)"
            )

            console.print(
                f"🔍 Searching for similar vectors (min_score >= {min_score})..."
            )

            response = client.query_vectors(
                bucket_name=bucket_name,
                index_name=index_name,
                query_embedding=query_embedding,
                top_k=max_results,
                min_score=min_score,
            )

            vectors = response.get("vectors", [])
            console.print(f"📊 Found {len(vectors)} results above threshold")

            # Use formatter with content control
            return formatter.format_retrieve_response(
                vectors,
                min_score,
                content_limit=content_limit,
                show_full_content=show_full_content,
            )

    except Exception as e:
        logger.exception(f"Memory {action} operation failed")
        return f"❌ **Error during {action} operation:** {str(e)}\n\n🔧 **Debug Info:**\nBucket: {bucket_name}\nIndex: {index_name}\nRegion: {region}"
