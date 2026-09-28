from database.content_repository import (
    ContentRepository,
)
from domain.artifacts import (
    Difficulty,
    GeneratedContent,
)
from content.fingerprint import (
    build_content_fingerprint,
)


def create_content(
    problem="Solve 3x = x^9",
    solution_steps=None,
):
    if solution_steps is None:
        solution_steps = (
            "Move all terms to one side",
            "Factor out x",
            "Solve the resulting equations",
        )

    return GeneratedContent(
        topic="Algebra",
        difficulty=Difficulty.MEDIUM,
        problem=problem,
        solution_steps=solution_steps,
        voice_script=(
            "First, move everything to one side."
        ),
        animation_spec={
            "actions": [
                {
                    "action": "write",
                    "expression": "3x = x^9",
                }
            ]
        },
    )


def test_same_content_has_same_fingerprint():
    first = create_content()
    second = create_content()

    assert (
        build_content_fingerprint(first)
        == build_content_fingerprint(second)
    )


def test_whitespace_does_not_change_fingerprint():
    first = create_content(
        problem="Solve 3x = x^9"
    )

    second = create_content(
        problem="  solve   3x = x^9  "
    )

    assert (
        build_content_fingerprint(first)
        == build_content_fingerprint(second)
    )


def test_different_problem_has_different_fingerprint():
    first = create_content(
        problem="Solve 3x = x^9"
    )

    second = create_content(
        problem="Solve 2x = x^5"
    )

    assert (
        build_content_fingerprint(first)
        != build_content_fingerprint(second)
    )


def test_content_repository_registers_once(
    tmp_path,
):
    database = tmp_path / "test.db"

    repository = ContentRepository(
        database
    )

    from database.repository import JobRepository

    JobRepository(database).initialize()

    content = create_content()

    assert repository.exists(content) is False

    assert repository.register(content) is True

    assert repository.exists(content) is True

    assert repository.register(content) is False


def test_mapper_converts_ai_schema_to_domain():
    from ai.mapper import to_domain_content
    from ai.schemas import GeneratedContentSchema

    schema = GeneratedContentSchema(
        topic="Algebra",
        difficulty="medium",
        problem="Solve 3x = x^9",
        solution_steps=[
            "Move all terms to one side",
            "Factor out x",
        ],
        voice_script=(
            "First, move everything to one side."
        ),
        animation_spec={
            "actions": [
                {
                    "action": "write",
                    "expression": "3x = x^9",
                },
                {
                    "action": "transform",
                    "from": "3x = x^9",
                    "to": "x(3-x^8)=0",
                },
            ]
        },
    )

    content = to_domain_content(schema)

    assert content.topic == "Algebra"
    assert content.difficulty == Difficulty.MEDIUM
    assert content.problem == "Solve 3x = x^9"

    assert len(content.solution_steps) == 2

    assert (
        content.animation_spec["actions"][1]["from"]
        == "3x = x^9"
    )
