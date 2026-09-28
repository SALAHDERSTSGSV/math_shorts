from __future__ import annotations

import sqlite3
from pathlib import Path

from domain.job import Job, JobStage, JobStatus


class JobRepository:
    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        schema_path = Path(__file__).with_name("schema.sql")

        with sqlite3.connect(self.database_path) as connection:
            connection.executescript(
                schema_path.read_text()
            )

    def create(self, job: Job) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO jobs (
                    id,
                    status,
                    current_stage,
                    retry_count,
                    error,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    job.status.value,
                    (
                        job.current_stage.value
                        if job.current_stage
                        else None
                    ),
                    job.retry_count,
                    job.error,
                    job.created_at.isoformat(),
                    job.updated_at.isoformat(),
                ),
            )

    def get(self, job_id: str) -> Job | None:
        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row

            row = connection.execute(
                """
                SELECT
                    id,
                    status,
                    current_stage,
                    retry_count,
                    error,
                    created_at,
                    updated_at
                FROM jobs
                WHERE id = ?
                """,
                (job_id,),
            ).fetchone()

        if row is None:
            return None

        job = Job(row["id"])

        job.status = JobStatus(row["status"])

        if row["current_stage"] is not None:
            job.current_stage = JobStage(
                row["current_stage"]
            )

        job.retry_count = row["retry_count"]
        job.error = row["error"]

        from datetime import datetime

        job.created_at = datetime.fromisoformat(
            row["created_at"]
        )

        job.updated_at = datetime.fromisoformat(
            row["updated_at"]
        )

        return job

    def update(self, job: Job) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                UPDATE jobs
                SET
                    status = ?,
                    current_stage = ?,
                    retry_count = ?,
                    error = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    job.status.value,
                    (
                        job.current_stage.value
                        if job.current_stage
                        else None
                    ),
                    job.retry_count,
                    job.error,
                    job.updated_at.isoformat(),
                    job.id,
                ),
            )

    def delete(self, job_id: str) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                DELETE FROM jobs
                WHERE id = ?
                """,
                (job_id,),
            )
