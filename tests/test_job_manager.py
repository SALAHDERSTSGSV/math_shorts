from domain.job import JobStatus
from database.repository import JobRepository
from orchestrator.job_manager import JobManager


def create_manager(tmp_path):
    database = tmp_path / "test.db"

    repository = JobRepository(database)
    repository.initialize()

    return JobManager(repository)


def test_create_job(tmp_path):
    manager = create_manager(tmp_path)

    job = manager.create_job("job-001")

    assert job.id == "job-001"
    assert job.status == JobStatus.PENDING


def test_get_job(tmp_path):
    manager = create_manager(tmp_path)

    manager.create_job("job-001")

    job = manager.get_job("job-001")

    assert job is not None
    assert job.id == "job-001"


def test_fail_and_retry_job(tmp_path):
    manager = create_manager(tmp_path)

    job = manager.create_job("job-001")

    job.transition_to(JobStatus.GENERATING)
    manager.save_job(job)

    manager.fail_job(
        job,
        "Gemini request failed",
    )

    assert job.status == JobStatus.FAILED
    assert job.error == "Gemini request failed"

    manager.retry_job(job)

    assert job.status == JobStatus.GENERATING
    assert job.retry_count == 1
    assert job.error is None
