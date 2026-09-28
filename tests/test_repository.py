from domain.job import Job, JobStatus
from database.repository import JobRepository


def test_job_persistence(tmp_path):
    database = tmp_path / "test.db"

    repository = JobRepository(database)
    repository.initialize()

    job = Job("job-001")

    repository.create(job)

    loaded = repository.get("job-001")

    assert loaded is not None
    assert loaded.id == "job-001"
    assert loaded.status == JobStatus.PENDING


def test_job_update(tmp_path):
    database = tmp_path / "test.db"

    repository = JobRepository(database)
    repository.initialize()

    job = Job("job-001")

    repository.create(job)

    job.transition_to(JobStatus.GENERATING)

    repository.update(job)

    loaded = repository.get("job-001")

    assert loaded is not None
    assert loaded.status == JobStatus.GENERATING
