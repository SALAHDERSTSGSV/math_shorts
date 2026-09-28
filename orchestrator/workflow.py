from __future__ import annotations

from collections.abc import Callable

from domain.job import Job, JobStatus
from orchestrator.job_manager import JobManager


class WorkflowError(Exception):
    pass


class Workflow:
    def __init__(self, job_manager: JobManager):
        self.job_manager = job_manager

    def run(
        self,
        job: Job,
        generate: Callable[[Job], None],
        verify: Callable[[Job], None],
        render: Callable[[Job], None],
        generate_audio: Callable[[Job], None],
        compose: Callable[[Job], None],
        qc: Callable[[Job], None],
    ) -> Job:

        stages = [
            (JobStatus.GENERATING, generate),
            (JobStatus.VERIFYING, verify),
            (JobStatus.RENDERING, render),
            (JobStatus.GENERATING_AUDIO, generate_audio),
            (JobStatus.COMPOSING, compose),
            (JobStatus.QC, qc),
        ]

        for index, (status, stage) in enumerate(stages):
            if job.status == JobStatus.FAILED:
                break

            if job.status == JobStatus.PENDING:
                job.transition_to(status)

            elif job.status != status:
                continue

            self.job_manager.save_job(job)

            try:
                stage(job)

            except Exception as exc:
                self.job_manager.fail_job(
                    job,
                    str(exc),
                )
                break

            # المرحلة نجحت.
            # إذا كانت آخر مرحلة، نحول مباشرة إلى COMPLETED.
            if status == JobStatus.QC:
                job.transition_to(JobStatus.COMPLETED)
                self.job_manager.save_job(job)
                break

            # الانتقال إلى المرحلة التالية.
            next_status = stages[index + 1][0]
            job.transition_to(next_status)
            self.job_manager.save_job(job)

        return job
