from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from content.fingerprint import (
    build_content_fingerprint,
)
from domain.artifacts import GeneratedContent


class ContentRepository:
    def __init__(
        self,
        database_path: str | Path,
    ):
        self.database_path = Path(
            database_path
        )

    def exists(
        self,
        content: GeneratedContent,
    ) -> bool:
        fingerprint = build_content_fingerprint(
            content
        )

        with sqlite3.connect(
            self.database_path
        ) as connection:
            row = connection.execute(
                """
                SELECT 1
                FROM generated_contents
                WHERE fingerprint = ?
                LIMIT 1
                """,
                (fingerprint,),
            ).fetchone()

        return row is not None

    def register(
        self,
        content: GeneratedContent,
    ) -> bool:
        fingerprint = build_content_fingerprint(
            content
        )

        created_at = datetime.now(
            timezone.utc
        ).isoformat()

        with sqlite3.connect(
            self.database_path
        ) as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO generated_contents (
                    fingerprint,
                    topic,
                    problem,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    fingerprint,
                    content.topic,
                    content.problem,
                    created_at,
                ),
            )

        return cursor.rowcount == 1
