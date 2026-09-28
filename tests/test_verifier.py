from domain.artifacts import Difficulty, GeneratedContent
from mathematics.verifier import MathVerifier


def create_content(
    problem: str,
    solution_steps: tuple[str, ...],
) -> GeneratedContent:

    return GeneratedContent(
        topic="Algebra",
        difficulty=Difficulty.MEDIUM,
        problem=problem,
        solution_steps=solution_steps,
        voice_script="Solve the equation step by step.",
        animation_spec={
            "actions": [
                {
                    "action": "write",
                    "expression": "3*x = x^9",
                }
            ]
        },
    )


def test_valid_equation_chain():
    content = create_content(
        "Solve 3*x = x^9",
        (
            "3*x = x^9",
            "x^9 - 3*x = 0",
            "x*(x^8 - 3) = 0",
        ),
    )

    result = MathVerifier().verify(content)

    assert result.valid is True
    assert "problem_expression_parsed" in result.checks
    assert "solution_expressions_valid" in result.checks
    assert "equation_transformations_valid" in result.checks
    assert "problem_solved_symbolically" in result.checks
    assert result.error is None


def test_invalid_transformation_is_rejected():
    content = create_content(
        "Solve 3*x = x^9",
        (
            "3*x = x^9",
            "x^9 - 3*x = 0",
            "x*(x^8 - 4) = 0",
        ),
    )

    result = MathVerifier().verify(content)

    assert result.valid is False
    assert result.error is not None
    assert "Invalid solution transformation" in result.error


def test_invalid_problem_is_rejected():
    content = create_content(
        "Explain why mathematics is useful",
        (
            "x = 2",
        ),
    )

    result = MathVerifier().verify(content)

    assert result.valid is False
    assert result.error is not None


def test_solver_finds_solution():
    content = create_content(
        "Solve x + 2 = 5",
        (
            "x + 2 = 5",
            "x = 3",
        ),
    )

    result = MathVerifier().verify(content)

    assert result.valid is True
    assert "3" in result.verified_solution
