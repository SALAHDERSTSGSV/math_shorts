from __future__ import annotations

from database.repository import JobRepository
from domain.job import Job


class JobManager:
    def __init__(self, repository: JobRepository):
        self.repository = repository

    def create_job(self, job_id: str) -> Job:
        job = Job(job_id)

        self.repository.create(job)

        return job

    def get_job(self, job_id: str) -> Job | None:
        return self.repository.get(job_id)

    def save_job(self, job: Job) -> None:
        self.repository.update(job)

    def fail_job(self, job: Job, error: str) -> None:
        job.fail(error)

        self.repository.update(job)

    def retry_job(self, job: Job) -> None:
        job.retry()

        self.repository.update(job)
