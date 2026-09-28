from database.repository import JobRepository
from domain.job import JobStatus
from orchestrator.job_manager import JobManager
from orchestrator.workflow import Workflow


def create_workflow(tmp_path):
    database = tmp_path / "test.db"

    repository = JobRepository(database)
    repository.initialize()

    manager = JobManager(repository)

    return Workflow(manager), manager


def test_workflow_completes(tmp_path):
    workflow, manager = create_workflow(tmp_path)

    job = manager.create_job("job-001")

    executed = []

    def generate(job):
        executed.append("generate")

    def verify(job):
        executed.append("verify")

    def render(job):
        executed.append("render")

    def generate_audio(job):
        executed.append("audio")

    def compose(job):
        executed.append("compose")

    def qc(job):
        executed.append("qc")

    result = workflow.run(
        job,
        generate,
        verify,
        render,
        generate_audio,
        compose,
        qc,
    )

    assert result.status == JobStatus.COMPLETED

    assert executed == [
        "generate",
        "verify",
        "render",
        "audio",
        "compose",
        "qc",
    ]


def test_workflow_stops_on_failure(tmp_path):
    workflow, manager = create_workflow(tmp_path)

    job = manager.create_job("job-001")

    executed = []

    def generate(job):
        executed.append("generate")

    def verify(job):
        executed.append("verify")
        raise RuntimeError("SymPy verification failed")

    def render(job):
        executed.append("render")

    def generate_audio(job):
        executed.append("audio")

    def compose(job):
        executed.append("compose")

    def qc(job):
        executed.append("qc")

    result = workflow.run(
        job,
        generate,
        verify,
        render,
        generate_audio,
        compose,
        qc,
    )

    assert result.status == JobStatus.FAILED
    assert result.current_stage.value == "verifying"
    assert result.error == "SymPy verification failed"

    assert executed == [
        "generate",
        "verify",
    ]
