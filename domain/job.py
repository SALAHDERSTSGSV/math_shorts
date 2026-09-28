from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    VERIFYING = "verifying"
    RENDERING = "rendering"
    GENERATING_AUDIO = "generating_audio"
    COMPOSING = "composing"
    QC = "qc"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStage(str, Enum):
    GENERATING = "generating"
    VERIFYING = "verifying"
    RENDERING = "rendering"
    GENERATING_AUDIO = "generating_audio"
    COMPOSING = "composing"
    QC = "qc"


ALLOWED_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.PENDING: {
        JobStatus.GENERATING,
        JobStatus.FAILED,
    },
    JobStatus.GENERATING: {
        JobStatus.VERIFYING,
        JobStatus.FAILED,
    },
    JobStatus.VERIFYING: {
        JobStatus.RENDERING,
        JobStatus.FAILED,
    },
    JobStatus.RENDERING: {
        JobStatus.GENERATING_AUDIO,
        JobStatus.FAILED,
    },
    JobStatus.GENERATING_AUDIO: {
        JobStatus.COMPOSING,
        JobStatus.FAILED,
    },
    JobStatus.COMPOSING: {
        JobStatus.QC,
        JobStatus.FAILED,
    },
    JobStatus.QC: {
        JobStatus.COMPLETED,
        JobStatus.FAILED,
    },
    JobStatus.COMPLETED: set(),
    JobStatus.FAILED: set(),
}


@dataclass
class Job:
    id: str

    status: JobStatus = JobStatus.PENDING

    current_stage: JobStage | None = None

    retry_count: int = 0

    error: str | None = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def transition_to(self, new_status: JobStatus) -> None:
        allowed = ALLOWED_TRANSITIONS[self.status]

        if new_status not in allowed:
            raise ValueError(
                f"Invalid job transition: "
                f"{self.status.value} -> {new_status.value}"
            )

        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

        if new_status == JobStatus.GENERATING:
            self.current_stage = JobStage.GENERATING

        elif new_status == JobStatus.VERIFYING:
            self.current_stage = JobStage.VERIFYING

        elif new_status == JobStatus.RENDERING:
            self.current_stage = JobStage.RENDERING

        elif new_status == JobStatus.GENERATING_AUDIO:
            self.current_stage = JobStage.GENERATING_AUDIO

        elif new_status == JobStatus.COMPOSING:
            self.current_stage = JobStage.COMPOSING

        elif new_status == JobStatus.QC:
            self.current_stage = JobStage.QC

        if new_status != JobStatus.FAILED:
            self.error = None

    def fail(self, error: str) -> None:
        if self.status == JobStatus.COMPLETED:
            raise ValueError("A completed job cannot fail.")

        self.status = JobStatus.FAILED
        self.error = error
        self.updated_at = datetime.now(timezone.utc)

    def retry(self) -> None:
        if self.status != JobStatus.FAILED:
            raise ValueError(
                "Only a failed job can be retried."
            )

        if self.current_stage is None:
            raise ValueError(
                "Cannot retry a job without a failed stage."
            )

        stage_to_status = {
            JobStage.GENERATING: JobStatus.GENERATING,
            JobStage.VERIFYING: JobStatus.VERIFYING,
            JobStage.RENDERING: JobStatus.RENDERING,
            JobStage.GENERATING_AUDIO: JobStatus.GENERATING_AUDIO,
            JobStage.COMPOSING: JobStatus.COMPOSING,
            JobStage.QC: JobStatus.QC,
        }

        self.status = stage_to_status[self.current_stage]
        self.retry_count += 1
        self.error = None
        self.updated_at = datetime.now(timezone.utc)
