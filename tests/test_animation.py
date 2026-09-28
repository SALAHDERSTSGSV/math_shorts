from ai.schemas import (
    AnimationAction,
    AnimationActionType,
    AnimationSpec,
    SceneObject,
    SceneObjectType,
    ScenePosition,
    )
from pathlib import Path

import pytest

from ai.schemas import (
    AnimationAction,
    AnimationActionType,
    AnimationSpec,
)
from animation.dsl import (
    AnimationDSL,
    AnimationValidationError,
    RenderOperationType,
)
from animation.engine import (
    AnimationEngine,
    CompiledAnimation,
)
from animation.manim_renderer import (
    ManimRenderer,
    ManimRendererError,
)


def test_write_action_compiles():
    spec = AnimationSpec(
        actions=[
            AnimationAction(
                action=AnimationActionType.WRITE,
                expression="3x = x^9",
                duration=1.5,
            )
        ]
    )

    compiled = AnimationEngine().compile(spec)

    assert compiled.operation_count == 1

    operation = compiled.operations[0]

    assert operation.type == RenderOperationType.WRITE
    assert operation.expression == "3x = x^9"
    assert operation.duration == 1.5


def test_transform_action_compiles():
    spec = AnimationSpec(
        actions=[
            AnimationAction(
                action=AnimationActionType.WRITE,
                expression="3x = x^9",
            ),
            AnimationAction(
                action=AnimationActionType.TRANSFORM,
                from_expression="3x = x^9",
                to_expression="x^9 - 3x = 0",
            ),
        ]
    )

    compiled = AnimationEngine().compile(spec)

    assert compiled.operation_count == 2

    transform = compiled.operations[1]

    assert transform.type == RenderOperationType.TRANSFORM
    assert transform.from_expression == "3x = x^9"
    assert transform.to_expression == "x^9 - 3x = 0"


def test_wait_requires_duration():
    with pytest.raises(ValueError):
        AnimationAction(
            action=AnimationActionType.WAIT,
        )


def test_highlight_requires_target():
    with pytest.raises(ValueError):
        AnimationAction(
            action=AnimationActionType.HIGHLIGHT,
        )


def test_fade_requires_target():
    with pytest.raises(ValueError):
        AnimationAction(
            action=AnimationActionType.FADE,
        )


def test_engine_rejects_empty_spec():
    with pytest.raises(ValueError):
        AnimationSpec(actions=[])


def test_engine_preserves_operation_order():
    spec = AnimationSpec(
        actions=[
            AnimationAction(
                action=AnimationActionType.WRITE,
                expression="3",
                duration=1,
            ),
            AnimationAction(
                action=AnimationActionType.WRITE,
                expression="3x",
                duration=1,
            ),
            AnimationAction(
                action=AnimationActionType.TRANSFORM,
                from_expression="3x",
                to_expression="3x = x^9",
                duration=2,
            ),
            AnimationAction(
                action=AnimationActionType.WAIT,
                duration=0.5,
            ),
        ]
    )

    compiled = AnimationEngine().compile(spec)

    assert [
        operation.type
        for operation in compiled.operations
    ] == [
        RenderOperationType.WRITE,
        RenderOperationType.WRITE,
        RenderOperationType.TRANSFORM,
        RenderOperationType.WAIT,
    ]

    assert compiled.estimated_duration == 4.5


def test_dsl_compiles_multiple_operations():
    spec = AnimationSpec(
        actions=[
            AnimationAction(
                action=AnimationActionType.WRITE,
                expression="3",
            ),
            AnimationAction(
                action=AnimationActionType.WRITE,
                expression="3x",
            ),
            AnimationAction(
                action=AnimationActionType.TRANSFORM,
                from_expression="3x",
                to_expression="3x = x^9",
            ),
        ]
    )

    operations = AnimationDSL().compile(spec)

    assert len(operations) == 3


def test_invalid_transform_is_rejected():
    with pytest.raises(ValueError):
        AnimationSpec(
            actions=[
                AnimationAction(
                    action=AnimationActionType.TRANSFORM,
                    from_expression="3x",
                )
            ]
        )


def test_unknown_action_cannot_reach_renderer():
    class FakeAction:
        action = "execute_python"

    with pytest.raises(
        AnimationValidationError
    ):
        AnimationDSL()._compile_action(
            FakeAction()
        )

def test_renderer_rejects_empty_animation(tmp_path):
    renderer = ManimRenderer(tmp_path)

    empty_animation = CompiledAnimation(
        objects=(),
        operations=(),
    )

    with pytest.raises(ManimRendererError):
        renderer.render(
            empty_animation,
            "test",
        )

def test_renderer_creates_scene_and_runs_manim(
    tmp_path,
    monkeypatch,
):

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

    captured = {}

    def fake_manim_run(
        command,
        capture_output,
        text,
        check,
    ):
        captured["command"] = command

        media_dir = Path(
            command[
                command.index("--media_dir") + 1
            ]
        )

        video_dir = (
            media_dir
            / "videos"
            / "generated_scene"
            / "1080p30"
        )

        video_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        (
            video_dir / "GeneratedScene.mp4"
        ).write_bytes(b"fake mp4")

        class Result:
            returncode = 0
            stdout = ""
            stderr = ""

        return Result()

    def fake_ffprobe_run(
        command,
        capture_output,
        text,
        check,
    ):

        class Result:
            returncode = 0

            stdout = (
                '{"streams":['
                '{"width":1080,'
                '"height":1920,'
                '"duration":"1.5"}'
                ']}'
            )

            stderr = ""

        return Result()

    def fake_run(
        command,
        capture_output,
        text,
        check,
    ):

        if command[0] == "ffprobe":
            return fake_ffprobe_run(
                command,
                capture_output,
                text,
                check,
            )

        return fake_manim_run(
            command,
            capture_output,
            text,
            check,
        )

    monkeypatch.setattr(
        "animation.manim_renderer.subprocess.run",
        fake_run,
    )

    monkeypatch.setattr(
        "video.probe.subprocess.run",
        fake_run,
    )

    monkeypatch.setattr(
        "video.probe.shutil.which",
        lambda command: "/usr/bin/ffprobe",
    )

    renderer = ManimRenderer(
        tmp_path,
        width=1080,
        height=1920,
        fps=30,
    )

    output = renderer.render(
        animation,
        "test_video",
    )

    assert output.path == str(
        tmp_path / "test_video.mp4"
    )

    assert output.duration_seconds == 1.5
    assert output.width == 1080
    assert output.height == 1920

    assert Path(output.path).exists()

    assert Path(
        output.path
    ).read_bytes() == b"fake mp4"

    command = captured["command"]

    assert "--resolution" in command
    assert "1080,1920" in command

    assert "--fps" in command
    assert "30" in command
def test_rich_scene_compiles():

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
            ),
            SceneObject(
                id="circle",
                type=SceneObjectType.CIRCLE,
                position=[2.5, -0.5, 0],
                color="GREEN",
                fill_opacity=0.65,
            ),
            SceneObject(
                id="triangle",
                type=SceneObjectType.TRIANGLE,
                position=[3.8, -1.4, 0],
                color="RED_E",
                fill_opacity=0.65,
                scale=1.2,
            ),
            SceneObject(
                id="equation",
                type=SceneObjectType.MATH,
                content=r"\oint_{\gamma} f(z)\,dz = 0",
                position=[3.2, -2.6, 0],
                font_size=42,
            ),
        ],
        animations=[
            AnimationAction(
                action=AnimationActionType.WRITE,
                target="title",
                duration=1.0,
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
            ),
        ],
    )

    compiled = AnimationEngine().compile(
        spec
    )

    assert compiled.object_count == 5
    assert compiled.operation_count == 5

    assert compiled.objects[0].id == "title"

    assert (
        compiled.operations[1].type
        == RenderOperationType.GROW
    )

    assert compiled.operations[1].targets == (
        "square",
        "circle",
        "triangle",
    )
