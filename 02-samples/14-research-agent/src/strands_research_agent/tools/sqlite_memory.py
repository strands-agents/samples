"""
SQLite-based memory tool with advanced search and organization capabilities.

This tool provides comprehensive memory management using SQLite as the backend,
leveraging SQLite's full-text search, JSON support, and advanced querying capabilities.
"""

import sqlite3
import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
from strands import tool


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
        else:
            return f"❌ Unknown action: {action}"

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


def _store_memory(
    conn: sqlite3.Connection,
    content: str,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    memory_id: Optional[str] = None,
) -> str:
    """Store a new memory entry."""
    if not content:
        return "❌ Content is required for storing memory"

    cursor = conn.cursor()

    # Generate ID if not provided
    if not memory_id:
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"

    # Generate content hash for deduplication
    content_hash = hashlib.sha256(content.encode()).hexdigest()

    # Check for duplicates
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

    # Store memory
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

    # Update tag counts
    if tags:
        for tag in tags:
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
    """Search memories using various search types."""
    if not query:
        return "❌ Query is required for searching"

    cursor = conn.cursor()
    results = []

    if search_type == "fulltext":
        # Use FTS5 for full-text search
        sql = """
            SELECT m.*, rank
            FROM memories_fts fts
            JOIN memories m ON m.id = fts.id
            WHERE memories_fts MATCH ?
            ORDER BY rank
        """
        cursor.execute(sql, (query,))
        results = cursor.fetchall()

    elif search_type == "exact":
        # Exact string matching
        sql = """
            SELECT * FROM memories 
            WHERE content LIKE ? OR title LIKE ?
            ORDER BY {}
        """.format(
            order_by
        )
        search_term = f"%{query}%"
        cursor.execute(sql, (search_term, search_term))
        results = cursor.fetchall()

    elif search_type == "fuzzy":
        # Simple fuzzy search using LIKE
        words = query.split()
        where_clauses = []
        params = []

        for word in words:
            where_clauses.append("(content LIKE ? OR title LIKE ?)")
            params.extend([f"%{word}%", f"%{word}%"])

        if where_clauses:
            sql = f"""
                SELECT * FROM memories 
                WHERE {' OR '.join(where_clauses)}
                ORDER BY {order_by}
            """
            cursor.execute(sql, params)
            results = cursor.fetchall()

    # Apply additional filters
    if filters and results:
        # This is a simple implementation - in production, you'd want to integrate filters into SQL
        filtered_results = []
        for result in results:
            match = True
            for key, value in filters.items():
                if key == "tags":
                    result_tags = json.loads(result["tags"])
                    if value not in result_tags:
                        match = False
                        break
                elif key in ["word_count", "char_count"]:
                    if isinstance(value, dict):
                        if "min" in value and result[key] < value["min"]:
                            match = False
                        if "max" in value and result[key] > value["max"]:
                            match = False
            if match:
                filtered_results.append(result)
        results = filtered_results

    # Apply pagination
    results = results[offset : offset + limit]

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
    """List all memories with optional filtering."""
    cursor = conn.cursor()

    # Build WHERE clause from filters
    where_clauses = []
    params = []

    if filters:
        for key, value in filters.items():
            if key == "tags":
                where_clauses.append("json_extract(tags, '$') LIKE ?")
                params.append(f'%"{value}"%')
            elif key in ["word_count", "char_count"]:
                if isinstance(value, dict):
                    if "min" in value:
                        where_clauses.append(f"{key} >= ?")
                        params.append(value["min"])
                    if "max" in value:
                        where_clauses.append(f"{key} <= ?")
                        params.append(value["max"])
            elif key == "created_after":
                where_clauses.append("created_at >= ?")
                params.append(value)
            elif key == "created_before":
                where_clauses.append("created_at <= ?")
                params.append(value)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Get total count
    cursor.execute(f"SELECT COUNT(*) as count FROM memories WHERE {where_sql}", params)
    total_count = cursor.fetchone()["count"]

    # Get memories
    sql = f"""
        SELECT * FROM memories 
        WHERE {where_sql}
        ORDER BY {order_by}
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
    """Get a specific memory by ID."""
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
            response += f"- {key}: {value}\n"
        response += "\n"

    response += f"📝 **Content:**\n{result['content']}"

    return response


def _delete_memory(conn: sqlite3.Connection, memory_id: str) -> str:
    """Delete a memory by ID."""
    if not memory_id:
        return "❌ Memory ID is required"

    cursor = conn.cursor()

    # Get memory details before deletion
    cursor.execute("SELECT title, tags FROM memories WHERE id = ?", (memory_id,))
    result = cursor.fetchone()

    if not result:
        return f"❌ Memory not found: {memory_id}"

    title = result["title"]
    tags = json.loads(result["tags"]) if result["tags"] else []

    # Update tag counts
    for tag in tags:
        cursor.execute(
            """
            UPDATE tags SET count = count - 1 WHERE name = ?
        """,
            (tag,),
        )
        # Remove tag if count reaches 0
        cursor.execute("DELETE FROM tags WHERE count <= 0")

    # Delete memory
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
    """Update an existing memory."""
    if not memory_id:
        return "❌ Memory ID is required"

    cursor = conn.cursor()

    # Check if memory exists
    cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
    existing = cursor.fetchone()

    if not existing:
        return f"❌ Memory not found: {memory_id}"

    # Build update fields
    updates = []
    params = []

    if content is not None:
        updates.extend(
            ["content = ?", "content_hash = ?", "word_count = ?", "char_count = ?"]
        )
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        word_count = len(content.split())
        char_count = len(content)
        params.extend([content, content_hash, word_count, char_count])

    if title is not None:
        updates.append("title = ?")
        params.append(title)

    if tags is not None:
        updates.append("tags = ?")
        params.append(json.dumps(tags))

        # Update tag counts
        old_tags = json.loads(existing["tags"]) if existing["tags"] else []

        # Decrease counts for removed tags
        for tag in old_tags:
            if tag not in tags:
                cursor.execute(
                    "UPDATE tags SET count = count - 1 WHERE name = ?", (tag,)
                )

        # Increase counts for new tags
        for tag in tags:
            if tag not in old_tags:
                cursor.execute(
                    """
                    INSERT INTO tags (name, count) VALUES (?, 1)
                    ON CONFLICT(name) DO UPDATE SET count = count + 1
                """,
                    (tag,),
                )

    if metadata is not None:
        updates.append("metadata = ?")
        params.append(json.dumps(metadata))

    if not updates:
        return "⚠️ No updates provided"

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(memory_id)

    # Execute update
    sql = f"UPDATE memories SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(sql, params)

    conn.commit()

    return f"""✅ **Memory updated successfully!**

🆔 **ID:** {memory_id}
📋 **Updated fields:** {len(updates) - 1}
📅 **Updated at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""


def _get_stats(conn: sqlite3.Connection) -> str:
    """Get database statistics."""
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

    # Top tags
    cursor.execute("SELECT name, count FROM tags ORDER BY count DESC LIMIT 10")
    top_tags = cursor.fetchall()

    # Recent activity
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
            response += f"- {tag['name']}: {tag['count']} memories\n"

    return response.strip()


def _export_memories(
    conn: sqlite3.Connection,
    export_format: str = "json",
    backup_path: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> str:
    """Export memories to various formats."""
    cursor = conn.cursor()

    # Get memories based on filters
    where_clauses = []
    params = []

    if filters:
        for key, value in filters.items():
            if key == "tags":
                where_clauses.append("json_extract(tags, '$') LIKE ?")
                params.append(f'%"{value}"%')

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

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

    # Determine export path
    if not backup_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"sqlite_memory_export_{timestamp}.{export_format}"

    # Export based on format
    if export_format == "json":
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(memories, f, indent=2, ensure_ascii=False, default=str)

    elif export_format == "csv":
        import csv

        with open(backup_path, "w", newline="", encoding="utf-8") as f:
            if memories:
                writer = csv.DictWriter(f, fieldnames=memories[0].keys())
                writer.writeheader()
                for memory in memories:
                    # Convert complex fields to strings for CSV
                    memory["tags"] = ", ".join(memory["tags"])
                    memory["metadata"] = json.dumps(memory["metadata"])
                    writer.writerow(memory)

    elif export_format == "sql":
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write("-- SQLite Memory Export\n")
            f.write("-- Generated: {}\n\n".format(datetime.now().isoformat()))

            for memory in memories:
                f.write(
                    "INSERT INTO memories (id, title, content, content_hash, tags, metadata, created_at, updated_at, word_count, char_count) VALUES (\n"
                )
                f.write(f"    {repr(memory['id'])},\n")
                f.write(f"    {repr(memory['title'])},\n")
                f.write(f"    {repr(memory['content'])},\n")
                f.write(f"    {repr(memory['content_hash'])},\n")
                f.write(f"    {repr(json.dumps(memory['tags']))},\n")
                f.write(f"    {repr(json.dumps(memory['metadata']))},\n")
                f.write(f"    {repr(memory['created_at'])},\n")
                f.write(f"    {repr(memory['updated_at'])},\n")
                f.write(f"    {memory['word_count']},\n")
                f.write(f"    {memory['char_count']}\n")
                f.write(");\n\n")

    return f"""✅ **Export completed successfully!**

📁 **File:** {backup_path}
📊 **Exported:** {len(memories)} memories
📋 **Format:** {export_format.upper()}
💾 **Size:** {os.path.getsize(backup_path)} bytes"""


def _import_memories(conn: sqlite3.Connection, backup_path: str) -> str:
    """Import memories from backup file."""
    if not backup_path or not os.path.exists(backup_path):
        return f"❌ Backup file not found: {backup_path}"

    try:
        with open(backup_path, "r", encoding="utf-8") as f:
            memories = json.load(f)

        cursor = conn.cursor()
        imported = 0
        skipped = 0

        for memory in memories:
            # Check if memory already exists
            cursor.execute("SELECT id FROM memories WHERE id = ?", (memory["id"],))
            if cursor.fetchone():
                skipped += 1
                continue

            # Insert memory
            cursor.execute(
                """
                INSERT INTO memories (id, title, content, content_hash, tags, metadata, 
                                    created_at, updated_at, word_count, char_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    memory["id"],
                    memory["title"],
                    memory["content"],
                    memory["content_hash"],
                    json.dumps(memory["tags"]),
                    json.dumps(memory["metadata"]),
                    memory["created_at"],
                    memory["updated_at"],
                    memory["word_count"],
                    memory["char_count"],
                ),
            )

            # Update tag counts
            for tag in memory["tags"]:
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
⏭️ **Skipped:** {skipped} (already exist)
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


def _execute_sql(conn: sqlite3.Connection, sql_query: Optional[str] = None) -> str:
    """Execute arbitrary SQL queries on the memory database."""
    if not sql_query:
        return "❌ SQL query is required"

    cursor = conn.cursor()

    try:
        # Clean and validate the query
        sql_query = sql_query.strip()
        if not sql_query:
            return "❌ Empty SQL query provided"

        # Determine if this is a read or write operation
        query_upper = sql_query.upper().strip()
        is_read_query = query_upper.startswith(("SELECT", "WITH", "PRAGMA", "EXPLAIN"))
        is_write_query = query_upper.startswith(
            ("INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER")
        )

        # Execute the query
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
                            # Truncate long strings
                            formatted_row.append(str(value)[:97] + "...")
                        else:
                            formatted_row.append(str(value))
                    response += "| " + " | ".join(formatted_row) + " |\n"

                if len(results) > 50:
                    response += f"\n*... and {len(results) - 50} more rows*"
            else:
                # Handle results without column descriptions
                for i, row in enumerate(results[:50], 1):
                    response += (
                        f"**Row {i}:** {dict(row) if hasattr(row, 'keys') else row}\n"
                    )

            return response

        elif is_write_query:
            # Handle INSERT, UPDATE, DELETE operations
            rows_affected = cursor.rowcount
            conn.commit()

            operation = query_upper.split()[0]
            return f"""✅ **SQL {operation} executed successfully!**

📊 **Results:**
- **Rows affected:** {rows_affected}
- **Operation:** {operation}
- **Query:** {sql_query[:100]}{'...' if len(sql_query) > 100 else ''}"""

        else:
            # Handle other operations (CREATE, DROP, etc.)
            conn.commit()
            return f"""✅ **SQL query executed successfully!**

📋 **Details:**
- **Query type:** {query_upper.split()[0] if query_upper else 'Unknown'}
- **Query:** {sql_query[:100]}{'...' if len(sql_query) > 100 else ''}"""

    except sqlite3.Error as e:
        # Handle SQLite-specific errors
        return f"""❌ **SQLite Error:**

🚫 **Error:** {str(e)}
📝 **Query:** {sql_query[:200]}{'...' if len(sql_query) > 200 else ''}

💡 **Common issues:**
- Check table/column names (use: `PRAGMA table_info(memories)`)
- Verify SQL syntax
- Ensure proper quoting for string values"""

    except Exception as e:
        # Handle other errors
        return f"""❌ **Query execution failed:**

🚫 **Error:** {str(e)}
📝 **Query:** {sql_query[:200]}{'...' if len(sql_query) > 200 else ''}"""
