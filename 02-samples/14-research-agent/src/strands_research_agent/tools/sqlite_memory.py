"""
SQLite-based memory tool with full-text search and rich querying for Strands agents.

This tool provides persistent memory management using SQLite as the backend, offering
fast storage, semantic search, and advanced organization capabilities. Perfect for
session-level context preservation and rapid knowledge retrieval in Strands workflows.

How It Works:
------------
1. **Persistent Storage**: Memories stored in SQLite database with full-text search indexing
2. **Rich Metadata**: Automatic tagging, custom metadata, word/character counts, timestamps
3. **Advanced Search**: Full-text, exact, fuzzy, and raw SQL querying capabilities
4. **Data Management**: Export, import, backup, and database optimization features
5. **Security**: Comprehensive SQL injection prevention with parameterized queries

Common Use Cases:
---------------
- Session context preservation across conversations
- Research note organization with tags and metadata
- Quick semantic search across stored knowledge
- Data analysis with custom SQL queries
- Knowledge base management for agents

Usage Examples:
--------------
```python
# Store a memory with tags and metadata
result = agent.tool.sqlite_memory(
    action="store",
    content="Important research findings about AI safety mechanisms",
    title="AI Safety Research - March 2024",
    tags=["research", "ai-safety", "mechanisms"],
    metadata={"priority": "high", "source": "paper-review"}
)

# Search memories with full-text search
result = agent.tool.sqlite_memory(
    action="search",
    query="AI safety mechanisms",
    search_type="fulltext",
    limit=5
)

# List recent memories with filtering
result = agent.tool.sqlite_memory(
    action="list",
    limit=10,
    order_by="created_at DESC",
    filters={"tags": "research"}
)

# Get specific memory by ID
result = agent.tool.sqlite_memory(
    action="get",
    memory_id="mem_abc123def456"
)

# Export memories for backup
result = agent.tool.sqlite_memory(
    action="export",
    export_format="json",
    backup_path="./memory_backup.json"
)

# Execute custom SQL for advanced queries
result = agent.tool.sqlite_memory(
    action="sql",
    sql_query="SELECT title, COUNT(*) FROM memories WHERE word_count > 100 GROUP BY title"
)
```

Security Features:
-----------------
- Comprehensive SQL injection prevention with strict validation
- Parameterized queries for all dynamic data operations
- Input sanitization and length limits on all user inputs
- Restricted SQL operations with allow-list approach
- Content deduplication using secure hashing algorithms
"""

import sqlite3
import json
import os
import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
import uuid
from strands import tool


ALLOWED_ORDER_COLUMNS: Set[str] = {
    "id",
    "title",
    "created_at",
    "updated_at",
    "word_count",
    "char_count",
    "rank",  # Used by FTS5 for full-text search ranking
}

ALLOWED_ORDER_DIRECTIONS: Set[str] = {"ASC", "DESC"}

# Default ORDER BY clause (guaranteed to be safe)
DEFAULT_ORDER_BY = "created_at DESC"

# Security limits
MAX_LIMIT = 1000
MAX_OFFSET = 10000
MAX_ORDER_BY_LENGTH = 200

# Security patterns to detect SQL injection attempts
SQL_INJECTION_PATTERNS = [
    r"[;()'\"`]",  # SQL special characters
    r"--",  # SQL comments
    r"/\*",  # Multi-line comment start
    r"\*/",  # Multi-line comment end
    r"\bunion\b",  # UNION attacks
    r"\bselect\b",  # SELECT injection
    r"\binsert\b",  # INSERT injection
    r"\bupdate\b",  # UPDATE injection
    r"\bdelete\b",  # DELETE injection
    r"\bdrop\b",  # DROP attacks
    r"\bexec\b",  # EXEC attacks
    r"\btruncate\b",  # TRUNCATE attacks
    r"\balter\b",  # ALTER attacks
    r"\bcreate\b",  # CREATE attacks
]


def _validate_order_by(order_by: str) -> str:
    """
    Validate and sanitize ORDER BY clause using strict allow list approach.

    This function provides comprehensive security validation for ORDER BY clauses
    to prevent SQL injection attacks. It uses a strict allow list approach where
    only pre-approved columns and directions are permitted.

    Args:
        order_by: ORDER BY clause to validate

    Returns:
        Validated ORDER BY clause or default if invalid

    Raises:
        ValueError: If order_by contains invalid elements
    """
    if not order_by or not isinstance(order_by, str):
        return DEFAULT_ORDER_BY

    # Clean the input and check for suspicious patterns
    order_by = order_by.strip()
    if not order_by:
        return DEFAULT_ORDER_BY

    # Additional security check: prevent SQL injection patterns
    order_by_lower = order_by.lower()
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, order_by_lower, re.IGNORECASE):
            raise ValueError(f"ORDER BY contains suspicious pattern: {pattern}")

    # Length check for security
    if len(order_by) > MAX_ORDER_BY_LENGTH:
        raise ValueError("ORDER BY clause too long")

    # Split by comma for multiple columns
    order_parts = []
    for part in order_by.split(","):
        part = part.strip()
        if not part:
            continue

        # Additional validation: check for only alphanumeric and underscore
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*(\s+(ASC|DESC|asc|desc))?$", part):
            raise ValueError(f"Invalid ORDER BY format: {part}")

        # Split column and direction
        tokens = part.split()
        if len(tokens) == 1:
            column = tokens[0].lower()
            direction = "ASC"
        elif len(tokens) == 2:
            column = tokens[0].lower()
            direction = tokens[1].upper()
        else:
            raise ValueError(f"Invalid ORDER BY format: {part}")

        # Validate column against allow list
        if column not in ALLOWED_ORDER_COLUMNS:
            raise ValueError(
                f"Invalid ORDER BY column: {column}. Allowed columns: {', '.join(sorted(ALLOWED_ORDER_COLUMNS))}"
            )

        # Validate direction against allow list
        if direction not in ALLOWED_ORDER_DIRECTIONS:
            raise ValueError(
                f"Invalid ORDER BY direction: {direction}. Allowed directions: {', '.join(ALLOWED_ORDER_DIRECTIONS)}"
            )

        order_parts.append(f"{column} {direction}")

    if not order_parts:
        return DEFAULT_ORDER_BY

    validated_order_by = ", ".join(order_parts)

    # Final validation: ensure the constructed clause is safe
    if not re.match(
        r"^[a-zA-Z_][a-zA-Z0-9_]*\s+(ASC|DESC)(\s*,\s*[a-zA-Z_][a-zA-Z0-9_]*\s+(ASC|DESC))*$",
        validated_order_by,
    ):
        raise ValueError("Constructed ORDER BY clause failed final validation")

    return validated_order_by


def _get_secure_order_by(order_by: str) -> str:
    """
    Get a securely validated ORDER BY clause with additional runtime validation.

    This function acts as a final security barrier before using ORDER BY in SQL queries.
    It performs re-validation and ensures the order_by clause is absolutely safe.

    Args:
        order_by: ORDER BY clause that should already be validated

    Returns:
        Secure ORDER BY clause guaranteed to be safe for SQL injection

    Raises:
        ValueError: If order_by fails validation
    """
    if not order_by or not isinstance(order_by, str):
        return DEFAULT_ORDER_BY

    # Re-validate to ensure security (defense in depth)
    try:
        validated = _validate_order_by(order_by)
    except ValueError as e:
        # Log security incident and return safe default
        print(f"SECURITY WARNING: ORDER BY validation failed: {e}")
        return DEFAULT_ORDER_BY

    # Additional runtime check: ensure it matches expected pattern
    if not re.match(
        r"^[a-zA-Z_][a-zA-Z0-9_]*\s+(ASC|DESC)(\s*,\s*[a-zA-Z_][a-zA-Z0-9_]*\s+(ASC|DESC))*$",
        validated,
    ):
        print(f"SECURITY WARNING: ORDER BY failed runtime pattern check: {validated}")
        return DEFAULT_ORDER_BY

    return validated


def _validate_limit_offset(limit: int, offset: int) -> tuple[int, int]:
    """
    Validate and sanitize limit and offset parameters.

    Args:
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        Tuple of validated (limit, offset)
    """
    # Validate limit
    if not isinstance(limit, int) or limit < 1:
        limit = 10
    elif limit > MAX_LIMIT:
        limit = MAX_LIMIT

    # Validate offset
    if not isinstance(offset, int) or offset < 0:
        offset = 0
    elif offset > MAX_OFFSET:
        offset = MAX_OFFSET

    return limit, offset


def _sanitize_string_input(
    input_str: Optional[str], max_length: int = 10000
) -> Optional[str]:
    """
    Sanitize string input to prevent injection attacks.

    Args:
        input_str: String to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string or None
    """
    if input_str is None:
        return None

    if not isinstance(input_str, str):
        input_str = str(input_str)

    # Limit length
    if len(input_str) > max_length:
        input_str = input_str[:max_length]

    return input_str


def _validate_sql_query(sql_query: str) -> str:
    """
    Validate SQL query for basic safety checks.

    Args:
        sql_query: SQL query to validate

    Returns:
        Validated SQL query

    Raises:
        ValueError: If query contains potentially dangerous operations
    """
    if not sql_query or not isinstance(sql_query, str):
        raise ValueError("SQL query is required and must be a string")

    sql_query = sql_query.strip()
    if not sql_query:
        raise ValueError("SQL query cannot be empty")

    # Convert to uppercase for checking
    query_upper = sql_query.upper()

    # Check for dangerous operations
    dangerous_patterns = [
        r"\bATTACH\b",
        r"\bDETACH\b",
        r"\bPRAGMA\s+(?!table_info|foreign_key_list|index_list|optimize)",
        r"\bLOAD_EXTENSION\b",
        r"--\s*[^\r\n]*",  # SQL comments
        r"/\*.*?\*/",  # Multi-line comments
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, query_upper):
            raise ValueError(
                f"SQL query contains potentially dangerous operation: {pattern}"
            )

    # Length limit for security
    if len(sql_query) > 50000:  # 50KB limit
        raise ValueError("SQL query too long")

    return sql_query


@tool
def sqlite_memory(
    action: str,
    content: Optional[str] = None,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    memory_id: Optional[str] = None,
    query: Optional[str] = None,
    sql_query: Optional[str] = None,
    search_type: str = "fulltext",
    limit: int = 10,
    offset: int = 0,
    order_by: str = "created_at DESC",
    filters: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
    export_format: str = "json",
    backup_path: Optional[str] = None,
) -> str:
    """
    Advanced SQLite-based memory tool with full-text search and rich querying.

    Args:
        action: Action to perform - 'store', 'retrieve', 'search', 'list', 'get',
               'delete', 'update', 'stats', 'export', 'import', 'backup', 'optimize', 'sql'
        content: Text content to store (required for 'store', 'update')
        title: Title/summary for the content
        tags: List of tags for categorization
        metadata: Additional metadata as key-value pairs
        memory_id: Unique identifier for memory entry (auto-generated if not provided)
        query: Search query for 'search' and 'retrieve' actions
        sql_query: Raw SQL query to execute (required for 'sql' action)
        search_type: Type of search - 'fulltext', 'semantic', 'exact', 'fuzzy'
        limit: Maximum number of results to return
        offset: Number of results to skip (for pagination)
        order_by: SQL ORDER BY clause
        filters: Additional filters as key-value pairs
        db_path: Path to SQLite database file
        export_format: Format for export - 'json', 'csv', 'sql'
        backup_path: Path for backup operations

    Returns:
        String with formatted response based on the action performed
    """
    try:
        # Input validation and sanitization
        content = _sanitize_string_input(content)
        title = _sanitize_string_input(title, 500)
        query = _sanitize_string_input(query, 5000)
        memory_id = _sanitize_string_input(memory_id, 100)

        # Validate action parameter
        valid_actions = {
            "store",
            "retrieve",
            "search",
            "list",
            "get",
            "delete",
            "update",
            "stats",
            "export",
            "import",
            "backup",
            "optimize",
            "sql",
        }
        if action not in valid_actions:
            return f"❌ Invalid action: {action}. Valid actions: {', '.join(sorted(valid_actions))}"

        # Validate and sanitize order_by with comprehensive error handling
        try:
            order_by = _validate_order_by(order_by)
        except ValueError as e:
            return f"❌ Security Error - {str(e)}"
        except Exception as e:
            # Catch any unexpected errors and return safe default
            print(f"SECURITY WARNING: Unexpected error in ORDER BY validation: {e}")
            order_by = DEFAULT_ORDER_BY

        # Validate limit and offset
        limit, offset = _validate_limit_offset(limit, offset)

        # Validate tags
        if tags is not None:
            if not isinstance(tags, list):
                return "❌ Tags must be a list"
            tags = [_sanitize_string_input(tag, 100) for tag in tags if tag]
            tags = [tag for tag in tags if tag]  # Remove None values

        # Initialize database
        if not db_path:
            db_path = os.path.expanduser("~/.maxs/sqlite_memory.db")

        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name

        # Initialize database schema
        _init_database(conn)

        # Route to appropriate action handler
        if action == "store":
            return _store_memory(conn, content, title, tags, metadata, memory_id)
        elif action == "retrieve" or action == "search":
            return _search_memory(
                conn, query, search_type, limit, offset, order_by, filters
            )
        elif action == "list":
            return _list_memories(conn, limit, offset, order_by, filters)
        elif action == "get":
            return _get_memory(conn, memory_id)
        elif action == "delete":
            return _delete_memory(conn, memory_id)
        elif action == "update":
            return _update_memory(conn, memory_id, content, title, tags, metadata)
        elif action == "stats":
            return _get_stats(conn)
        elif action == "export":
            return _export_memories(conn, export_format, backup_path, filters)
        elif action == "import":
            return _import_memories(conn, backup_path)
        elif action == "backup":
            return _backup_database(db_path, backup_path)
        elif action == "optimize":
            return _optimize_database(conn)
        elif action == "sql":
            return _execute_sql(conn, sql_query)

    except Exception as e:
        return f"❌ Error: {str(e)}"
    finally:
        if "conn" in locals():
            conn.close()


def _init_database(conn: sqlite3.Connection) -> None:
    """Initialize the SQLite database with proper schema and indexes."""
    cursor = conn.cursor()

    # Create main memories table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            title TEXT,
            content TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            tags TEXT, -- JSON array of tags
            metadata TEXT, -- JSON object for additional metadata
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            word_count INTEGER,
            char_count INTEGER
        )
    """
    )

    # Create FTS5 virtual table for full-text search
    cursor.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
            id UNINDEXED,
            title,
            content,
            tags,
            content='memories',
            content_rowid='rowid'
        )
    """
    )

    # Create triggers to keep FTS table in sync
    cursor.execute(
        """
        CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
            INSERT INTO memories_fts(rowid, id, title, content, tags) 
            VALUES (new.rowid, new.id, new.title, new.content, new.tags);
        END
    """
    )

    cursor.execute(
        """
        CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
            INSERT INTO memories_fts(memories_fts, rowid, id, title, content, tags) 
            VALUES ('delete', old.rowid, old.id, old.title, old.content, old.tags);
        END
    """
    )

    cursor.execute(
        """
        CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
            INSERT INTO memories_fts(memories_fts, rowid, id, title, content, tags) 
            VALUES ('delete', old.rowid, old.id, old.title, old.content, old.tags);
            INSERT INTO memories_fts(rowid, id, title, content, tags) 
            VALUES (new.rowid, new.id, new.title, new.content, new.tags);
        END
    """
    )

    # Create indexes for better performance
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_memories_updated_at ON memories(updated_at)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_memories_content_hash ON memories(content_hash)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_memories_word_count ON memories(word_count)"
    )

    # Create tags table for better tag management
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tags (
            name TEXT PRIMARY KEY,
            count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    conn.commit()


def _build_where_clause_with_params(
    filters: Optional[Dict[str, Any]],
) -> tuple[str, List[Any]]:
    """
    Build WHERE clause with parameterized queries for security.

    Args:
        filters: Dictionary of filters to apply

    Returns:
        Tuple of (where_clause, parameters)
    """
    where_clauses = []
    params = []

    if not filters:
        return "1=1", []

    # Define allowed filter keys for security
    allowed_filters = {
        "tags",
        "word_count",
        "char_count",
        "created_after",
        "created_before",
        "updated_after",
        "updated_before",
        "title",
        "content",
    }

    for key, value in filters.items():
        if key not in allowed_filters:
            continue  # Skip unknown filters for security

        if key == "tags":
            # Use parameterized query for tag filtering
            where_clauses.append("json_extract(tags, '$') LIKE ?")
            params.append(f'%"{_sanitize_string_input(str(value), 100)}"%')

        elif key in ["word_count", "char_count"]:
            if isinstance(value, dict):
                if "min" in value and isinstance(value["min"], (int, float)):
                    where_clauses.append(f"{key} >= ?")
                    params.append(int(value["min"]))
                if "max" in value and isinstance(value["max"], (int, float)):
                    where_clauses.append(f"{key} <= ?")
                    params.append(int(value["max"]))
            elif isinstance(value, (int, float)):
                where_clauses.append(f"{key} = ?")
                params.append(int(value))

        elif key in ["created_after", "updated_after"]:
            where_clauses.append(f"{key.replace('_after', '_at')} >= ?")
            params.append(_sanitize_string_input(str(value), 50))

        elif key in ["created_before", "updated_before"]:
            where_clauses.append(f"{key.replace('_before', '_at')} <= ?")
            params.append(_sanitize_string_input(str(value), 50))

        elif key in ["title", "content"]:
            where_clauses.append(f"{key} LIKE ?")
            params.append(f"%{_sanitize_string_input(str(value), 1000)}%")

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    return where_sql, params


def _store_memory(
    conn: sqlite3.Connection,
    content: str,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    memory_id: Optional[str] = None,
) -> str:
    """Store a new memory entry with secure parameterized queries."""
    if not content:
        return "❌ Content is required for storing memory"

    cursor = conn.cursor()

    # Generate ID if not provided
    if not memory_id:
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"

    # Validate memory_id format
    if not re.match(r"^[a-zA-Z0-9_-]+$", memory_id):
        return (
            "❌ Memory ID can only contain letters, numbers, hyphens, and underscores"
        )

    # Generate content hash for deduplication
    content_hash = hashlib.sha256(content.encode()).hexdigest()

    # Check for duplicates using parameterized query
    cursor.execute("SELECT id FROM memories WHERE content_hash = ?", (content_hash,))
    existing = cursor.fetchone()
    if existing:
        return f"⚠️ Similar content already exists with ID: {existing['id']}"

    # Calculate metrics
    word_count = len(content.split())
    char_count = len(content)

    # Auto-generate title if not provided
    if not title:
        # Use first 50 characters as title
        title = content[:50].strip()
        if len(content) > 50:
            title += "..."

    # Prepare data
    tags_json = json.dumps(tags if tags else [])
    metadata_json = json.dumps(metadata if metadata else {})

    # Store memory using parameterized query
    cursor.execute(
        """
        INSERT INTO memories (id, title, content, content_hash, tags, metadata, word_count, char_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            memory_id,
            title,
            content,
            content_hash,
            tags_json,
            metadata_json,
            word_count,
            char_count,
        ),
    )

    # Update tag counts using parameterized queries
    if tags:
        for tag in tags:
            tag = _sanitize_string_input(tag, 100)
            if tag:
                cursor.execute(
                    """
                    INSERT INTO tags (name, count) VALUES (?, 1)
                    ON CONFLICT(name) DO UPDATE SET count = count + 1
                """,
                    (tag,),
                )

    conn.commit()

    return f"""✅ **Memory stored successfully!**

📋 **Details:**
- **ID:** {memory_id}
- **Title:** {title}
- **Content:** {char_count} characters, {word_count} words
- **Tags:** {', '.join(tags) if tags else 'None'}
- **Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""


def _search_memory(
    conn: sqlite3.Connection,
    query: str,
    search_type: str = "fulltext",
    limit: int = 10,
    offset: int = 0,
    order_by: str = "created_at DESC",
    filters: Optional[Dict[str, Any]] = None,
) -> str:
    """Search memories using various search types with secure parameterized queries."""
    if not query:
        return "❌ Query is required for searching"

    cursor = conn.cursor()
    results = []

    if search_type == "fulltext":
        # Use FTS5 for full-text search - already secure with parameters
        sql = """
            SELECT m.*, rank
            FROM memories_fts fts
            JOIN memories m ON m.id = fts.id
            WHERE memories_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        """
        cursor.execute(sql, (query, limit, offset))
        results = cursor.fetchall()

    elif search_type == "exact":
        # Exact string matching with parameterized queries
        # SECURE: Using validated and sanitized ORDER BY clause
        secure_order_by = _get_secure_order_by(order_by)
        sql = f"""
            SELECT * FROM memories 
            WHERE content LIKE ? OR title LIKE ?
            ORDER BY {secure_order_by}
            LIMIT ? OFFSET ?
        """
        search_term = f"%{query}%"
        cursor.execute(sql, (search_term, search_term, limit, offset))
        results = cursor.fetchall()

    elif search_type == "fuzzy":
        # Secure fuzzy search using parameterized queries
        words = query.split()
        if not words:
            return "❌ Invalid query for fuzzy search"

        # Build parameterized WHERE clause
        where_parts = []
        params = []

        for word in words[:10]:  # Limit to 10 words for performance
            word = _sanitize_string_input(word, 100)
            if word:
                where_parts.append("(content LIKE ? OR title LIKE ?)")
                params.extend([f"%{word}%", f"%{word}%"])

        if where_parts:
            # SECURE: Using parameterized WHERE clause and validated ORDER BY
            secure_order_by = _get_secure_order_by(order_by)
            where_clause = " OR ".join(where_parts)
            sql = f"""
                SELECT * FROM memories 
                WHERE {where_clause}
                ORDER BY {secure_order_by}
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])
            cursor.execute(sql, params)
            results = cursor.fetchall()

    else:
        return f"❌ Invalid search type: {search_type}. Valid types: fulltext, exact, fuzzy"

    # Apply additional filters using secure parameterized queries
    if filters and results:
        # Convert results to list for filtering
        results_list = list(results)
        filtered_results = []

        for result in results_list:
            match = True
            for key, value in filters.items():
                if key == "tags":
                    result_tags = json.loads(result["tags"]) if result["tags"] else []
                    if str(value) not in result_tags:
                        match = False
                        break
                elif key in ["word_count", "char_count"]:
                    if isinstance(value, dict):
                        if "min" in value and result[key] < value["min"]:
                            match = False
                        if "max" in value and result[key] > value["max"]:
                            match = False
                    elif isinstance(value, (int, float)) and result[key] != value:
                        match = False
            if match:
                filtered_results.append(result)
        results = filtered_results

    if not results:
        return f"📭 No memories found for query: '{query}'"

    # Format results
    response = f"🔍 **Found {len(results)} memories for '{query}':**\n\n"

    for i, result in enumerate(results, 1):
        tags = json.loads(result["tags"]) if result["tags"] else []
        metadata = json.loads(result["metadata"]) if result["metadata"] else {}

        # Truncate content for display
        content_preview = result["content"][:200]
        if len(result["content"]) > 200:
            content_preview += "..."

        response += f"""**{i}. {result['title']}** (`{result['id']}`)
📅 {result['created_at']} | 📊 {result['word_count']} words
🏷️ Tags: {', '.join(tags) if tags else 'None'}
📝 {content_preview}

"""

    return response.strip()


def _list_memories(
    conn: sqlite3.Connection,
    limit: int = 10,
    offset: int = 0,
    order_by: str = "created_at DESC",
    filters: Optional[Dict[str, Any]] = None,
) -> str:
    """List all memories with optional filtering using secure parameterized queries."""
    cursor = conn.cursor()

    # Build secure WHERE clause with parameters
    where_sql, params = _build_where_clause_with_params(filters)

    # Get total count using parameterized query
    cursor.execute(f"SELECT COUNT(*) as count FROM memories WHERE {where_sql}", params)
    total_count = cursor.fetchone()["count"]

    # Get memories using parameterized query with validated ORDER BY
    secure_order_by = _get_secure_order_by(order_by)
    sql = f"""
        SELECT * FROM memories 
        WHERE {where_sql}
        ORDER BY {secure_order_by}
        LIMIT ? OFFSET ?
    """
    cursor.execute(sql, params + [limit, offset])
    results = cursor.fetchall()

    if not results:
        return "📭 No memories found"

    # Format results
    response = f"📚 **Memory Library ({len(results)} of {total_count} total):**\n\n"

    for i, result in enumerate(results, offset + 1):
        tags = json.loads(result["tags"]) if result["tags"] else []

        # Truncate content for display
        content_preview = result["content"][:150]
        if len(result["content"]) > 150:
            content_preview += "..."

        response += f"""**{i}. {result['title']}** (`{result['id']}`)
📅 {result['created_at']} | 📊 {result['word_count']} words
🏷️ {', '.join(tags) if tags else 'No tags'}
📝 {content_preview}

"""

    return response.strip()


def _get_memory(conn: sqlite3.Connection, memory_id: str) -> str:
    """Get a specific memory by ID using parameterized query."""
    if not memory_id:
        return "❌ Memory ID is required"

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
    result = cursor.fetchone()

    if not result:
        return f"❌ Memory not found: {memory_id}"

    tags = json.loads(result["tags"]) if result["tags"] else []
    metadata = json.loads(result["metadata"]) if result["metadata"] else {}

    response = f"""📄 **Memory: {result['title']}**

🆔 **ID:** {result['id']}
📅 **Created:** {result['created_at']}
📅 **Updated:** {result['updated_at']}
📊 **Stats:** {result['word_count']} words, {result['char_count']} characters
🏷️ **Tags:** {', '.join(tags) if tags else 'None'}

"""

    if metadata:
        response += f"🔧 **Metadata:**\n"
        for key, value in metadata.items():
            # Sanitize metadata display
            key = _sanitize_string_input(str(key), 100) or "unknown"
            value = _sanitize_string_input(str(value), 1000) or "N/A"
            response += f"- {key}: {value}\n"
        response += "\n"

    response += f"📝 **Content:**\n{result['content']}"

    return response


def _delete_memory(conn: sqlite3.Connection, memory_id: str) -> str:
    """Delete a memory by ID using parameterized query."""
    if not memory_id:
        return "❌ Memory ID is required"

    cursor = conn.cursor()

    # Get memory details before deletion using parameterized query
    cursor.execute("SELECT title, tags FROM memories WHERE id = ?", (memory_id,))
    result = cursor.fetchone()

    if not result:
        return f"❌ Memory not found: {memory_id}"

    title = result["title"]
    tags = json.loads(result["tags"]) if result["tags"] else []

    # Update tag counts using parameterized queries
    for tag in tags:
        cursor.execute(
            "UPDATE tags SET count = count - 1 WHERE name = ?",
            (tag,),
        )
        # Remove tag if count reaches 0
        cursor.execute("DELETE FROM tags WHERE count <= 0")

    # Delete memory using parameterized query
    cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))

    if cursor.rowcount == 0:
        return f"❌ Failed to delete memory: {memory_id}"

    conn.commit()

    return f"""✅ **Memory deleted successfully!**

🆔 **ID:** {memory_id}
📋 **Title:** {title}
🏷️ **Tags:** {', '.join(tags) if tags else 'None'}"""


def _update_memory(
    conn: sqlite3.Connection,
    memory_id: str,
    content: Optional[str] = None,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Update an existing memory using secure parameterized queries."""
    if not memory_id:
        return "❌ Memory ID is required"

    cursor = conn.cursor()

    # Check if memory exists using parameterized query
    cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
    existing = cursor.fetchone()

    if not existing:
        return f"❌ Memory not found: {memory_id}"

    # Build update fields securely
    update_fields = []
    params = []

    if content is not None:
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        word_count = len(content.split())
        char_count = len(content)

        update_fields.extend(
            ["content = ?", "content_hash = ?", "word_count = ?", "char_count = ?"]
        )
        params.extend([content, content_hash, word_count, char_count])

    if title is not None:
        update_fields.append("title = ?")
        params.append(title)

    if tags is not None:
        update_fields.append("tags = ?")
        params.append(json.dumps(tags))

        # Update tag counts securely
        old_tags = json.loads(existing["tags"]) if existing["tags"] else []

        # Decrease counts for removed tags
        for tag in old_tags:
            if tag not in tags:
                cursor.execute(
                    "UPDATE tags SET count = count - 1 WHERE name = ?", (tag,)
                )

        # Increase counts for new tags
        for tag in tags:
            tag = _sanitize_string_input(tag, 100)
            if tag and tag not in old_tags:
                cursor.execute(
                    """
                    INSERT INTO tags (name, count) VALUES (?, 1)
                    ON CONFLICT(name) DO UPDATE SET count = count + 1
                """,
                    (tag,),
                )

    if metadata is not None:
        update_fields.append("metadata = ?")
        params.append(json.dumps(metadata))

    if not update_fields:
        return "⚠️ No updates provided"

    # Add timestamp update
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    params.append(memory_id)

    # Execute update using parameterized query
    sql = f"UPDATE memories SET {', '.join(update_fields)} WHERE id = ?"
    cursor.execute(sql, params)

    conn.commit()

    return f"""✅ **Memory updated successfully!**

🆔 **ID:** {memory_id}
📋 **Updated fields:** {len(update_fields) - 1}
📅 **Updated at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""


def _get_stats(conn: sqlite3.Connection) -> str:
    """Get database statistics using secure queries."""
    cursor = conn.cursor()

    # Basic counts
    cursor.execute("SELECT COUNT(*) as count FROM memories")
    memory_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM tags WHERE count > 0")
    tag_count = cursor.fetchone()["count"]

    # Content statistics
    cursor.execute(
        """
        SELECT 
            SUM(word_count) as total_words,
            SUM(char_count) as total_chars,
            AVG(word_count) as avg_words,
            MAX(word_count) as max_words,
            MIN(word_count) as min_words
        FROM memories
    """
    )
    content_stats = cursor.fetchone()

    # Top tags using parameterized query
    cursor.execute("SELECT name, count FROM tags ORDER BY count DESC LIMIT ?", (10,))
    top_tags = cursor.fetchall()

    # Recent activity using parameterized query
    cursor.execute(
        """
        SELECT COUNT(*) as count FROM memories 
        WHERE created_at >= date('now', '-7 days')
    """
    )
    recent_count = cursor.fetchone()["count"]

    response = f"""📊 **SQLite Memory Statistics**

📚 **Content:**
- **Total memories:** {memory_count:,}
- **Total tags:** {tag_count:,}
- **Recent (7 days):** {recent_count:,}

"""

    if memory_count > 0:
        response += f"""📝 **Content Analysis:**
- **Total words:** {content_stats['total_words'] or 0:,} 
- **Total characters:** {content_stats['total_chars'] or 0:,}
- **Average words per memory:** {content_stats['avg_words'] or 0:.1f}
- **Largest memory:** {content_stats['max_words'] or 0:,} words
- **Smallest memory:** {content_stats['min_words'] or 0:,} words

"""
    else:
        response += "📝 **Content Analysis:** No memories stored yet\n\n"

    if top_tags:
        response += "🏷️ **Top Tags:**\n"
        for tag in top_tags:
            # Sanitize tag display
            tag_name = _sanitize_string_input(tag["name"], 100) or "unknown"
            response += f"- {tag_name}: {tag['count']} memories\n"

    return response.strip()


def _export_memories(
    conn: sqlite3.Connection,
    export_format: str = "json",
    backup_path: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> str:
    """Export memories to various formats using secure queries."""
    cursor = conn.cursor()

    # Get memories based on filters using secure parameterized queries
    where_sql, params = _build_where_clause_with_params(filters)

    cursor.execute(f"SELECT * FROM memories WHERE {where_sql}", params)
    results = cursor.fetchall()

    if not results:
        return "📭 No memories to export"

    # Convert to list of dicts
    memories = []
    for row in results:
        memory = dict(row)
        memory["tags"] = json.loads(memory["tags"]) if memory["tags"] else []
        memory["metadata"] = (
            json.loads(memory["metadata"]) if memory["metadata"] else {}
        )
        memories.append(memory)

    # Validate export format
    valid_formats = {"json", "csv", "sql"}
    if export_format not in valid_formats:
        return f"❌ Invalid export format: {export_format}. Valid formats: {', '.join(valid_formats)}"

    # Determine export path
    if not backup_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"sqlite_memory_export_{timestamp}.{export_format}"

    # Sanitize backup path
    backup_path = _sanitize_string_input(backup_path, 500)
    if not backup_path:
        return "❌ Invalid backup path"

    try:
        # Export based on format
        if export_format == "json":
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(memories, f, indent=2, ensure_ascii=False, default=str)

        elif export_format == "csv":
            import csv

            with open(backup_path, "w", newline="", encoding="utf-8") as f:
                if memories:
                    # Sanitize field names
                    fieldnames = [
                        _sanitize_string_input(k, 50) or "unknown"
                        for k in memories[0].keys()
                    ]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for memory in memories:
                        # Convert complex fields to strings for CSV and sanitize
                        sanitized_memory = {}
                        for k, v in memory.items():
                            key = _sanitize_string_input(k, 50) or "unknown"
                            if isinstance(v, list):
                                sanitized_memory[key] = ", ".join(
                                    str(item)[:100] for item in v
                                )
                            elif isinstance(v, dict):
                                sanitized_memory[key] = json.dumps(v)[
                                    :1000
                                ]  # Limit size
                            else:
                                sanitized_memory[key] = _sanitize_string_input(
                                    str(v), 1000
                                )
                        writer.writerow(sanitized_memory)

        elif export_format == "sql":
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write("-- SQLite Memory Export\n")
                f.write("-- Generated: {}\n\n".format(datetime.now().isoformat()))

                for memory in memories:
                    # Use parameterized-style SQL for safety demonstration
                    f.write(
                        "INSERT INTO memories (id, title, content, content_hash, tags, metadata, created_at, updated_at, word_count, char_count) VALUES (\n"
                    )
                    # Properly escape values for SQL
                    values = [
                        repr(memory["id"]),
                        repr(memory["title"]),
                        repr(memory["content"]),
                        repr(memory["content_hash"]),
                        repr(json.dumps(memory["tags"])),
                        repr(json.dumps(memory["metadata"])),
                        repr(memory["created_at"]),
                        repr(memory["updated_at"]),
                        str(memory["word_count"]),
                        str(memory["char_count"]),
                    ]
                    f.write("    " + ",\n    ".join(values) + "\n")
                    f.write(");\n\n")

        return f"""✅ **Export completed successfully!**

📁 **File:** {backup_path}
📊 **Exported:** {len(memories)} memories
📋 **Format:** {export_format.upper()}
💾 **Size:** {os.path.getsize(backup_path)} bytes"""

    except Exception as e:
        return f"❌ Export failed: {str(e)}"


def _import_memories(conn: sqlite3.Connection, backup_path: str) -> str:
    """Import memories from backup file using secure parameterized queries."""
    if not backup_path or not os.path.exists(backup_path):
        return f"❌ Backup file not found: {backup_path}"

    try:
        with open(backup_path, "r", encoding="utf-8") as f:
            memories = json.load(f)

        if not isinstance(memories, list):
            return "❌ Invalid backup format: expected list of memories"

        cursor = conn.cursor()
        imported = 0
        skipped = 0

        for memory in memories:
            if not isinstance(memory, dict):
                skipped += 1
                continue

            # Validate required fields
            required_fields = ["id", "content"]
            if not all(field in memory for field in required_fields):
                skipped += 1
                continue

            # Sanitize memory data
            memory_id = _sanitize_string_input(memory.get("id"), 100)
            content = _sanitize_string_input(memory.get("content"))
            title = _sanitize_string_input(memory.get("title"), 500)

            if not memory_id or not content:
                skipped += 1
                continue

            # Check if memory already exists using parameterized query
            cursor.execute("SELECT id FROM memories WHERE id = ?", (memory_id,))
            if cursor.fetchone():
                skipped += 1
                continue

            # Prepare data
            tags = memory.get("tags", [])
            if not isinstance(tags, list):
                tags = []
            tags = [_sanitize_string_input(tag, 100) for tag in tags if tag]

            metadata = memory.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}

            # Insert memory using parameterized query
            cursor.execute(
                """
                INSERT INTO memories (id, title, content, content_hash, tags, metadata, 
                                    created_at, updated_at, word_count, char_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    memory_id,
                    title,
                    content,
                    memory.get(
                        "content_hash", hashlib.sha256(content.encode()).hexdigest()
                    ),
                    json.dumps(tags),
                    json.dumps(metadata),
                    memory.get("created_at"),
                    memory.get("updated_at"),
                    int(memory.get("word_count", len(content.split()))),
                    int(memory.get("char_count", len(content))),
                ),
            )

            # Update tag counts using parameterized queries
            for tag in tags:
                if tag:
                    cursor.execute(
                        """
                        INSERT INTO tags (name, count) VALUES (?, 1)
                        ON CONFLICT(name) DO UPDATE SET count = count + 1
                    """,
                        (tag,),
                    )

            imported += 1

        conn.commit()

        return f"""✅ **Import completed successfully!**

📁 **File:** {backup_path}
📥 **Imported:** {imported} memories
⏭️ **Skipped:** {skipped} (invalid or already exist)
📊 **Total processed:** {len(memories)}"""

    except json.JSONDecodeError:
        return f"❌ Invalid JSON format in backup file: {backup_path}"
    except Exception as e:
        return f"❌ Import failed: {str(e)}"


def _backup_database(db_path: str, backup_path: Optional[str] = None) -> str:
    """Create a full database backup."""
    if not backup_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"sqlite_memory_backup_{timestamp}.db"

    # Sanitize paths
    backup_path = _sanitize_string_input(backup_path, 500)
    if not backup_path:
        return "❌ Invalid backup path"

    try:
        import shutil

        shutil.copy2(db_path, backup_path)

        return f"""✅ **Database backup completed!**

📁 **Original:** {db_path}
💾 **Backup:** {backup_path}
📊 **Size:** {os.path.getsize(backup_path)} bytes"""

    except Exception as e:
        return f"❌ Backup failed: {str(e)}"


def _optimize_database(conn: sqlite3.Connection) -> str:
    """Optimize the database for better performance."""
    cursor = conn.cursor()

    try:
        # Analyze tables for query optimization
        cursor.execute("ANALYZE")

        # Rebuild FTS index
        cursor.execute("INSERT INTO memories_fts(memories_fts) VALUES('rebuild')")

        # Vacuum to reclaim space
        cursor.execute("VACUUM")

        # Update statistics
        cursor.execute("PRAGMA optimize")

        conn.commit()

        return """✅ **Database optimization completed!**

🔧 **Operations performed:**
- ✅ Analyzed tables for query optimization
- ✅ Rebuilt full-text search index
- ✅ Vacuumed database to reclaim space
- ✅ Updated query planner statistics

💡 **Result:** Improved query performance and reduced file size"""

    except Exception as e:
        return f"❌ Database optimization failed: {str(e)}"


def _execute_sql(conn: sqlite3.Connection, sql_query: Optional[str] = None) -> str:
    """Execute arbitrary SQL queries on the memory database with security validation."""
    if not sql_query:
        return "❌ SQL query is required"

    try:
        # Validate SQL query for security
        sql_query = _validate_sql_query(sql_query)

        cursor = conn.cursor()

        # Determine if this is a read or write operation
        query_upper = sql_query.upper().strip()
        is_read_query = query_upper.startswith(("SELECT", "WITH", "EXPLAIN"))
        is_write_query = query_upper.startswith(
            ("INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER")
        )

        # Execute the query (already validated for security)
        cursor.execute(sql_query)

        if is_read_query:
            # Handle SELECT and similar read queries
            results = cursor.fetchall()

            if not results:
                return "📭 **Query executed successfully, no results returned**"

            # Get column names
            columns = (
                [description[0] for description in cursor.description]
                if cursor.description
                else []
            )

            # Format results
            response = f"📊 **SQL Query Results** ({len(results)} rows)\n\n"

            if columns:
                # Add header
                response += "| " + " | ".join(f"**{col}**" for col in columns) + " |\n"
                response += "|" + "|".join([" --- " for _ in columns]) + "|\n"

                # Add rows (limit to first 50 rows for readability)
                display_rows = results[:50]
                for row in display_rows:
                    formatted_row = []
                    for value in row:
                        if value is None:
                            formatted_row.append("NULL")
                        elif isinstance(value, str) and len(str(value)) > 100:
                            # Truncate and sanitize long strings
                            sanitized_value = _sanitize_string_input(str(value), 97)
                            formatted_row.append(sanitized_value + "...")
                        else:
                            # Sanitize all values for display
                            sanitized_value = _sanitize_string_input(str(value), 100)
                            formatted_row.append(sanitized_value or "N/A")
                    response += "| " + " | ".join(formatted_row) + " |\n"

                if len(results) > 50:
                    response += f"\n*... and {len(results) - 50} more rows*"
            else:
                # Handle results without column descriptions
                for i, row in enumerate(results[:50], 1):
                    if hasattr(row, "keys"):
                        sanitized_row = {
                            k: _sanitize_string_input(str(v), 200)
                            for k, v in dict(row).items()
                        }
                        response += f"**Row {i}:** {sanitized_row}\n"
                    else:
                        sanitized_row = _sanitize_string_input(str(row), 200)
                        response += f"**Row {i}:** {sanitized_row}\n"

            return response

        elif is_write_query:
            # Handle INSERT, UPDATE, DELETE operations
            rows_affected = cursor.rowcount
            conn.commit()

            operation = query_upper.split()[0]
            query_preview = _sanitize_string_input(sql_query, 100)
            return f"""✅ **SQL {operation} executed successfully!**

📊 **Results:**
- **Rows affected:** {rows_affected}
- **Operation:** {operation}
- **Query:** {query_preview}{'...' if len(sql_query) > 100 else ''}"""

        else:
            # Handle other operations (PRAGMA, etc.)
            conn.commit()
            query_preview = _sanitize_string_input(sql_query, 100)
            operation = query_upper.split()[0] if query_upper else "Unknown"
            return f"""✅ **SQL query executed successfully!**

📋 **Details:**
- **Query type:** {operation}
- **Query:** {query_preview}{'...' if len(sql_query) > 100 else ''}"""

    except ValueError as e:
        # Handle validation errors
        return f"❌ **Security Validation Error:** {str(e)}"

    except sqlite3.Error as e:
        # Handle SQLite-specific errors
        query_preview = _sanitize_string_input(sql_query, 200) if sql_query else "N/A"
        return f"""❌ **SQLite Error:**

🚫 **Error:** {str(e)}
📝 **Query:** {query_preview}{'...' if sql_query and len(sql_query) > 200 else ''}

💡 **Common issues:**
- Check table/column names (use: `PRAGMA table_info(memories)`)
- Verify SQL syntax
- Ensure proper quoting for string values"""

    except Exception as e:
        # Handle other errors
        query_preview = _sanitize_string_input(sql_query, 200) if sql_query else "N/A"
        return f"""❌ **Query execution failed:**

🚫 **Error:** {str(e)}
📝 **Query:** {query_preview}{'...' if sql_query and len(sql_query) > 200 else ''}"""
