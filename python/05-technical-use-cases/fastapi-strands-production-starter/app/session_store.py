"""SQLite-backed session store built on the shipped ``RepositorySessionManager``.

The Strands SDK ships File, S3, and Repository session managers, among others;
SQLite is not a first-party one, so this module provides it by implementing the
``SessionRepository`` interface (8 CRUD methods) and combining it with
``RepositorySessionManager`` — the same pattern the built-in ``FileSessionManager``
uses. Sessions, agents, and per-message rows are persisted in a single SQLite
database file so conversations survive process restarts.

Schema
------
- ``sessions(session_id PK, data JSON)``
- ``agents(session_id, agent_id, data JSON, PK(session_id, agent_id))``
- ``messages(session_id, agent_id, message_id, data JSON, PK(session_id, agent_id, message_id))``

``data`` holds the ``to_dict()`` payload of each record (already
base64-encoded for bytes by the SDK), serialized as JSON.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from typing import Any

from strands.session.repository_session_manager import RepositorySessionManager
from strands.session.session_repository import SessionRepository
from strands.types.exceptions import SessionException
from strands.types.session import Session, SessionAgent, SessionMessage


class SQLiteSessionManager(RepositorySessionManager, SessionRepository):
    """Persist Strands agent sessions in a local SQLite database.

    Combines ``RepositorySessionManager`` (session lifecycle wiring the agent
    uses) with a ``SessionRepository`` implementation backed by SQLite.
    """

    def __init__(self, session_id: str, db_path: str = "sessions.db", **kwargs: Any) -> None:
        """Initialize the SQLite session manager.

        Args:
            session_id: ID for the session; created if it does not exist yet.
            db_path: Path to the SQLite database file.
            **kwargs: Additional keyword arguments for future extensibility.
        """
        self.db_path = db_path
        # SQLite connections are not shareable across threads by default; a lock
        # keeps the single connection safe under FastAPI's threadpool/async use.
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_tables()

        super().__init__(session_id=session_id, session_repository=self, **kwargs)

    def _create_tables(self) -> None:
        with self._lock, self._conn:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS agents (
                    session_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    data TEXT NOT NULL,
                    PRIMARY KEY (session_id, agent_id)
                );
                CREATE TABLE IF NOT EXISTS messages (
                    session_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    message_id INTEGER NOT NULL,
                    data TEXT NOT NULL,
                    PRIMARY KEY (session_id, agent_id, message_id)
                );
                """
            )

    # --- Session ---------------------------------------------------------

    def create_session(self, session: Session, **kwargs: Any) -> Session:
        """Create a new session; raises if it already exists."""
        with self._lock, self._conn:
            existing = self._conn.execute(
                "SELECT 1 FROM sessions WHERE session_id = ?", (session.session_id,)
            ).fetchone()
            if existing:
                raise SessionException(f"Session {session.session_id} already exists")
            self._conn.execute(
                "INSERT INTO sessions (session_id, data) VALUES (?, ?)",
                (session.session_id, json.dumps(session.to_dict())),
            )
        return session

    def read_session(self, session_id: str, **kwargs: Any) -> Session | None:
        """Read a session, or None when it does not exist."""
        with self._lock:
            row = self._conn.execute(
                "SELECT data FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        if row is None:
            return None
        return Session.from_dict(json.loads(row[0]))

    # --- Agent -----------------------------------------------------------

    def create_agent(self, session_id: str, session_agent: SessionAgent, **kwargs: Any) -> None:
        """Create a new agent within a session."""
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO agents (session_id, agent_id, data) VALUES (?, ?, ?)",
                (session_id, session_agent.agent_id, json.dumps(session_agent.to_dict())),
            )

    def read_agent(self, session_id: str, agent_id: str, **kwargs: Any) -> SessionAgent | None:
        """Read an agent, or None when it does not exist."""
        with self._lock:
            row = self._conn.execute(
                "SELECT data FROM agents WHERE session_id = ? AND agent_id = ?",
                (session_id, agent_id),
            ).fetchone()
        if row is None:
            return None
        return SessionAgent.from_dict(json.loads(row[0]))

    def update_agent(self, session_id: str, session_agent: SessionAgent, **kwargs: Any) -> None:
        """Update an agent, preserving its original created_at timestamp."""
        previous = self.read_agent(session_id=session_id, agent_id=session_agent.agent_id)
        if previous is None:
            raise SessionException(
                f"Agent {session_agent.agent_id} in session {session_id} does not exist"
            )
        session_agent.created_at = previous.created_at
        with self._lock, self._conn:
            self._conn.execute(
                "UPDATE agents SET data = ? WHERE session_id = ? AND agent_id = ?",
                (json.dumps(session_agent.to_dict()), session_id, session_agent.agent_id),
            )

    # --- Message ---------------------------------------------------------

    def create_message(
        self, session_id: str, agent_id: str, session_message: SessionMessage, **kwargs: Any
    ) -> None:
        """Create a new message for an agent."""
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO messages "
                "(session_id, agent_id, message_id, data) VALUES (?, ?, ?, ?)",
                (
                    session_id,
                    agent_id,
                    session_message.message_id,
                    json.dumps(session_message.to_dict()),
                ),
            )

    def read_message(
        self, session_id: str, agent_id: str, message_id: int, **kwargs: Any
    ) -> SessionMessage | None:
        """Read a single message, or None when it does not exist."""
        with self._lock:
            row = self._conn.execute(
                "SELECT data FROM messages "
                "WHERE session_id = ? AND agent_id = ? AND message_id = ?",
                (session_id, agent_id, message_id),
            ).fetchone()
        if row is None:
            return None
        return SessionMessage.from_dict(json.loads(row[0]))

    def update_message(
        self, session_id: str, agent_id: str, session_message: SessionMessage, **kwargs: Any
    ) -> None:
        """Update a message, preserving its original created_at timestamp."""
        previous = self.read_message(
            session_id=session_id, agent_id=agent_id, message_id=session_message.message_id
        )
        if previous is None:
            raise SessionException(f"Message {session_message.message_id} does not exist")
        session_message.created_at = previous.created_at
        with self._lock, self._conn:
            self._conn.execute(
                "UPDATE messages SET data = ? "
                "WHERE session_id = ? AND agent_id = ? AND message_id = ?",
                (
                    json.dumps(session_message.to_dict()),
                    session_id,
                    agent_id,
                    session_message.message_id,
                ),
            )

    def list_messages(
        self,
        session_id: str,
        agent_id: str,
        limit: int | None = None,
        offset: int = 0,
        **kwargs: Any,
    ) -> list[SessionMessage]:
        """List messages for an agent, ordered by message_id, with pagination."""
        query = (
            "SELECT data FROM messages WHERE session_id = ? AND agent_id = ? "
            "ORDER BY message_id ASC"
        )
        params: list[Any] = [session_id, agent_id]
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        elif offset:
            query += " LIMIT -1 OFFSET ?"
            params.append(offset)
        with self._lock:
            rows = self._conn.execute(query, params).fetchall()
        return [SessionMessage.from_dict(json.loads(row[0])) for row in rows]

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        with self._lock:
            self._conn.close()
