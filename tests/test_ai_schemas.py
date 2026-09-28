import pytest
from pydantic import ValidationError

from ai.schemas import (
    AnimationActionType,
    GeneratedContentSchema,
)


def valid_content():
    return {
        "topic": "Algebra",
        "difficulty": "medium",
        "problem": "Solve 3x = x^9",
        "solution_steps": [
            "Move all terms to one side",
            "Factor out x",
            "Solve each resulting equation",
        ],
        "voice_script": (
            "First, move everything to one side. "
            "Then factor out x."
        ),
        "animation_spec": {
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
    }


def test_valid_generated_content():
    content = GeneratedContentSchema.model_validate(
        valid_content()
    )

    assert content.topic == "Algebra"
    assert content.difficulty.value == "medium"
    assert len(content.animation_spec.actions) == 2


def test_unknown_top_level_field_is_rejected():
    data = valid_content()
    data["unexpected"] = "bad"

    with pytest.raises(ValidationError):
        GeneratedContentSchema.model_validate(data)


def test_write_requires_expression():
    data = valid_content()

    data["animation_spec"]["actions"] = [
        {
            "action": "write",
        }
    ]

    with pytest.raises(ValidationError):
        GeneratedContentSchema.model_validate(data)


def test_transform_requires_from_and_to():
    data = valid_content()

    data["animation_spec"]["actions"] = [
        {
            "action": "transform",
            "from": "x = 1",
        }
    ]

    with pytest.raises(ValidationError):
        GeneratedContentSchema.model_validate(data)


def test_unknown_animation_action_is_rejected():
    data = valid_content()

    data["animation_spec"]["actions"] = [
        {
            "action": "delete_everything",
        }
    ]

    with pytest.raises(ValidationError):
        GeneratedContentSchema.model_validate(data)


def test_empty_solution_step_is_rejected():
    data = valid_content()

    data["solution_steps"] = [
        "Valid step",
        "",
    ]

    with pytest.raises(ValidationError):
        GeneratedContentSchema.model_validate(data)
