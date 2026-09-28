from pathlib import Path

import pytest

from ai.schemas import (
    AnimationAction,
    AnimationActionType,
    AnimationSpec,
    SceneObject,
    SceneObjectType,
    ScenePosition,
)
from animation.engine import AnimationEngine
from animation.manim_renderer import ManimRenderer


@pytest.mark.integration
def test_real_rich_manim_render():

    spec = AnimationSpec(
        objects=[
            SceneObject(
                id="title",
                type=SceneObjectType.TEXT,
                content="Manim",
                position=ScenePosition.TOP,
                font_size=80,
                font="DejaVu Serif",
            ),
            SceneObject(
                id="square",
                type=SceneObjectType.SQUARE,
                position=[3.5, 1.0, 0],
                color="BLUE_E",
                fill_opacity=0.65,
                stroke_width=2,
            ),
            SceneObject(
                id="circle",
                type=SceneObjectType.CIRCLE,
                position=[2.5, -0.4, 0],
                color="GREEN",
                fill_opacity=0.65,
                stroke_width=2,
            ),
            SceneObject(
                id="triangle",
                type=SceneObjectType.TRIANGLE,
                position=[3.8, -1.4, 0],
                color="RED_E",
                fill_opacity=0.65,
                stroke_width=2,
                scale=1.3,
            ),
            SceneObject(
                id="subtitle",
                type=SceneObjectType.TEXT,
                content="All systems operational!",
                position=ScenePosition.BOTTOM,
                font_size=36,
                font="DejaVu Serif",
            ),
            SceneObject(
                id="equation",
                type=SceneObjectType.MATH,
                content=r"\oint_{\gamma} f(z)\,dz = 0",
                position=[3.2, -2.4, 0],
                font_size=42,
            ),
        ],
        animations=[
            AnimationAction(
                action=AnimationActionType.WRITE,
                target="title",
                duration=1.2,
            ),
            AnimationAction(
                action=AnimationActionType.GROW,
                targets=[
                    "square",
                    "circle",
                    "triangle",
                ],
                duration=1.4,
                lag_ratio=0.15,
            ),
            AnimationAction(
                action=AnimationActionType.FADE_IN,
                target="subtitle",
                duration=0.8,
            ),
            AnimationAction(
                action=AnimationActionType.WRITE,
                target="equation",
                duration=1.0,
            ),
            AnimationAction(
                action=AnimationActionType.HIGHLIGHT,
                target="equation",
                duration=0.5,
            ),
            AnimationAction(
                action=AnimationActionType.INDICATE,
                target="equation",
                duration=0.8,
                scale_factor=1.12,
            ),
            AnimationAction(
                action=AnimationActionType.WAIT,
                duration=0.8,
            ),
            AnimationAction(
                action=AnimationActionType.FADE_OUT,
                targets=[
                    "title",
                    "subtitle",
                    "square",
                    "circle",
                    "triangle",
                    "equation",
                ],
                duration=0.8,
            ),
        ],
    )

    animation = AnimationEngine().compile(
        spec
    )

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
        "rich_math_test",
    )

    output = Path(
        rendered.path
    )

    assert output.exists()
    assert output.is_file()
    assert output.stat().st_size > 0

    assert rendered.width == 1080
    assert rendered.height == 1920

    assert rendered.duration_seconds > 5
