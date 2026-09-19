"""Persistência das sessões de comunicação e dos eventos de letras."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from database.db import DB_PATH


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


@dataclass(frozen=True)
class CommunicationEvent:
    id: int
    session_id: str
    event_type: str
    predicted_letter: str | None
    confidence: float | None
    confirmed_letter: str | None
    corrected: bool
    source: str
    model_version: str | None
    created_at: str
    facial_expression: str | None = None
    facial_confidence: float | None = None
    facial_model_version: str | None = None


class CommunicationRepository:
    """Acesso SQLite isolado do protótipo legado de captura de pontos."""

    def __init__(self, database_path: str | Path = DB_PATH) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS communication_sessions (
                    id TEXT PRIMARY KEY,
                    started_at TEXT NOT NULL,
                    ended_at TEXT
                );

                CREATE TABLE IF NOT EXISTS communication_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL
                        CHECK (event_type IN ('letter', 'space', 'backspace', 'clear')),
                    predicted_letter TEXT,
                    confidence REAL,
                    confirmed_letter TEXT,
                    corrected INTEGER NOT NULL CHECK (corrected IN (0, 1)),
                    source TEXT NOT NULL CHECK (source IN ('manual', 'recognizer')),
                    model_version TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id)
                        REFERENCES communication_sessions(id)
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_communication_events_session
                    ON communication_events(session_id, id);
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(communication_events)").fetchall()
            }
            migrations = {
                "facial_expression": "ALTER TABLE communication_events ADD COLUMN facial_expression TEXT",
                "facial_confidence": "ALTER TABLE communication_events ADD COLUMN facial_confidence REAL",
                "facial_model_version": "ALTER TABLE communication_events ADD COLUMN facial_model_version TEXT",
            }
            for column, statement in migrations.items():
                if column not in columns:
                    connection.execute(statement)

    def create_session(self) -> str:
        session_id = str(uuid4())
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO communication_sessions (id, started_at) VALUES (?, ?)",
                (session_id, _utc_now()),
            )
        return session_id

    def session_exists(self, session_id: str) -> bool:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT 1 FROM communication_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        return row is not None

    def add_event(
        self,
        *,
        session_id: str,
        event_type: str,
        confirmed_letter: str | None,
        predicted_letter: str | None,
        confidence: float | None,
        source: str,
        model_version: str | None,
        facial_expression: str | None = None,
        facial_confidence: float | None = None,
        facial_model_version: str | None = None,
    ) -> CommunicationEvent:
        corrected = predicted_letter is not None and predicted_letter != confirmed_letter
        created_at = _utc_now()
        with self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO communication_events (
                    session_id,
                    event_type,
                    predicted_letter,
                    confidence,
                    confirmed_letter,
                    corrected,
                    source,
                    model_version,
                    created_at,
                    facial_expression,
                    facial_confidence,
                    facial_model_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    event_type,
                    predicted_letter,
                    confidence,
                    confirmed_letter,
                    int(corrected),
                    source,
                    model_version,
                    created_at,
                    facial_expression,
                    facial_confidence,
                    facial_model_version,
                ),
            )
            event_id = int(cursor.lastrowid)

        return CommunicationEvent(
            id=event_id,
            session_id=session_id,
            event_type=event_type,
            predicted_letter=predicted_letter,
            confidence=confidence,
            confirmed_letter=confirmed_letter,
            corrected=corrected,
            source=source,
            model_version=model_version,
            created_at=created_at,
            facial_expression=facial_expression,
            facial_confidence=facial_confidence,
            facial_model_version=facial_model_version,
        )

    def list_events(self, session_id: str) -> list[CommunicationEvent]:
        with self._connection() as connection:
            rows: Iterable[sqlite3.Row] = connection.execute(
                """
                SELECT
                    id,
                    session_id,
                    event_type,
                    predicted_letter,
                    confidence,
                    confirmed_letter,
                    corrected,
                    source,
                    model_version,
                    created_at,
                    facial_expression,
                    facial_confidence,
                    facial_model_version
                FROM communication_events
                WHERE session_id = ?
                ORDER BY id
                """,
                (session_id,),
            ).fetchall()

        return [
            CommunicationEvent(
                id=row["id"],
                session_id=row["session_id"],
                event_type=row["event_type"],
                predicted_letter=row["predicted_letter"],
                confidence=row["confidence"],
                confirmed_letter=row["confirmed_letter"],
                corrected=bool(row["corrected"]),
                source=row["source"],
                model_version=row["model_version"],
                created_at=row["created_at"],
                facial_expression=row["facial_expression"],
                facial_confidence=row["facial_confidence"],
                facial_model_version=row["facial_model_version"],
            )
            for row in rows
        ]
