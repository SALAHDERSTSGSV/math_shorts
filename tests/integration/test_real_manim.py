from pathlib import Path

import pytest

from ai.schemas import (
    AnimationAction,
    AnimationActionType,
    AnimationSpec,
)
from animation.engine import AnimationEngine
from animation.manim_renderer import ManimRenderer


@pytest.mark.integration
def test_real_manim_render():

    spec = AnimationSpec(
        actions=[
            AnimationAction(
                action=AnimationActionType.WRITE,
                expression="3",
                duration=0.5,
            ),
            AnimationAction(
                action=AnimationActionType.WRITE,
                expression="3x",
                duration=0.5,
            ),
            AnimationAction(
                action=AnimationActionType.TRANSFORM,
                from_expression="3x",
                to_expression="3x = x^9",
                duration=0.5,
            ),
        ]
    )

    animation = AnimationEngine().compile(spec)

    output_directory = Path(
        "tests/integration/output"
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    renderer = ManimRenderer(
        output_directory,
        width=1080,
        height=1920,
        fps=30,
    )

    rendered = renderer.render(
        animation,
        "real_math_test",
    )

    output = Path(rendered.path)

    assert output.exists()
    assert output.is_file()
    assert output.stat().st_size > 0

    assert output.suffix == ".mp4"

    assert rendered.width == 1080
    assert rendered.height == 1920

    assert rendered.duration_seconds >= 1.0
