from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from animation.dsl import (
    RenderOperation,
    RenderOperationType,
)
from animation.engine import CompiledAnimation
from domain.artifacts import RenderedVideo
from video.probe import VideoProbe


class ManimRendererError(Exception):
    """Raised when Manim rendering fails."""


class ManimRenderer:
    """
    Renders a compiled animation scene using Manim.

    Gemini
        ↓
    JSON
        ↓
    Pydantic
        ↓
    AnimationDSL
        ↓
    CompiledAnimation
        ↓
    ManimRenderer
        ↓
    MP4
    """

    def __init__(
        self,
        output_directory: str | Path,
        *,
        width: int = 1080,
        height: int = 1920,
        fps: int = 30,
        manim_command: str = "manim",
    ):
        self.output_directory = Path(
            output_directory
        )

        self.width = width
        self.height = height
        self.fps = fps
        self.manim_command = manim_command

        self.video_probe = VideoProbe()

    def render(
        self,
        animation: CompiledAnimation,
        video_name: str,
    ) -> RenderedVideo:

        if not animation.operations:
            raise ManimRendererError(
                "Cannot render an empty animation."
            )

        if shutil.which(
            self.manim_command
        ) is None:
            raise ManimRendererError(
                f"Manim executable not found: "
                f"{self.manim_command}"
            )

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        safe_name = self._safe_video_name(
            video_name
        )

        with tempfile.TemporaryDirectory(
            prefix="math_shorts_manim_"
        ) as temp_directory:

            temp_directory = Path(
                temp_directory
            )

            scene_file = (
                temp_directory
                / "generated_scene.py"
            )

            media_directory = (
                temp_directory
                / "media"
            )

            payload = self._serialize_animation(
                animation
            )

            scene_file.write_text(
                self._build_scene_source(
                    payload
                ),
                encoding="utf-8",
            )

            command = [
                self.manim_command,
                "--media_dir",
                str(media_directory),
                "--resolution",
                f"{self.width},{self.height}",
                "--fps",
                str(self.fps),
                str(scene_file),
                "GeneratedScene",
            ]

            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=False,
                )

            except OSError as exc:
                raise ManimRendererError(
                    f"Failed to execute Manim: {exc}"
                ) from exc

            if result.returncode != 0:
                raise ManimRendererError(
                    "Manim rendering failed.\n"
                    f"stdout:\n{result.stdout}\n"
                    f"stderr:\n{result.stderr}"
                )

            source_video = (
                self._find_rendered_video(
                    media_directory
                )
            )

            if source_video is None:
                raise ManimRendererError(
                    "Manim completed successfully but "
                    "no MP4 video was found.\n"
                    f"media directory: {media_directory}\n"
                    f"stdout:\n{result.stdout}\n"
                    f"stderr:\n{result.stderr}"
                )

            final_path = (
                self.output_directory
                / f"{safe_name}.mp4"
            )

            shutil.copy2(
                source_video,
                final_path,
            )

        metadata = self.video_probe.probe(
            final_path
        )

        if metadata.width != self.width:
            raise ManimRendererError(
                f"Unexpected rendered width: "
                f"{metadata.width}"
            )

        if metadata.height != self.height:
            raise ManimRendererError(
                f"Unexpected rendered height: "
                f"{metadata.height}"
            )

        return RenderedVideo(
            path=str(final_path),
            duration_seconds=metadata.duration_seconds,
            width=metadata.width,
            height=metadata.height,
        )

    def _find_rendered_video(
        self,
        media_directory: Path,
    ) -> Path | None:

        if not media_directory.exists():
            return None

        candidates = sorted(
            media_directory.rglob("*.mp4"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

        if not candidates:
            return None

        return candidates[0]

    def _safe_video_name(
        self,
        name: str,
    ) -> str:

        cleaned = "".join(
            character
            if character.isalnum()
            or character in "_-"
            else "_"
            for character in name
        )

        if not cleaned:
            raise ManimRendererError(
                "Video name cannot be empty."
            )

        return cleaned

    def _serialize_animation(
        self,
        animation: CompiledAnimation,
    ) -> dict:

        objects = []

        for obj in animation.objects:

            position = obj.position

            if isinstance(
                position,
                tuple,
            ):
                position = list(position)

            elif hasattr(
                position,
                "value",
            ):
                position = position.value

            objects.append(
                {
                    "id": obj.id,
                    "type": obj.type.value,
                    "content": obj.content,
                    "position": position,
                    "font_size": obj.font_size,
                    "font": obj.font,
                    "color": obj.color,
                    "fill_opacity": obj.fill_opacity,
                    "stroke_width": obj.stroke_width,
                    "scale": obj.scale,
                }
            )

        operations = []

        for operation in animation.operations:

            operations.append(
                {
                    "type": operation.type.value,
                    "expression": operation.expression,
                    "from_expression": (
                        operation.from_expression
                    ),
                    "to_expression": (
                        operation.to_expression
                    ),
                    "target": operation.target,
                    "targets": list(
                        operation.targets
                    ),
                    "duration": operation.duration,
                    "lag_ratio": operation.lag_ratio,
                    "scale_factor": (
                        operation.scale_factor
                    ),
                }
            )

        return {
            "objects": objects,
            "operations": operations,
        }

    def _build_scene_source(
        self,
        payload: dict,
    ) -> str:

        payload_source = repr(payload)

        return f'''
from manim import *


SCENE_DATA = {payload_source}


COLOR_MAP = {{
    "WHITE": WHITE,
    "BLACK": BLACK,
    "BLUE": BLUE,
    "BLUE_E": BLUE_E,
    "GREEN": GREEN,
    "GREEN_E": GREEN_E,
    "RED": RED,
    "RED_E": RED_E,
    "YELLOW": YELLOW,
    "ORANGE": ORANGE,
    "PURPLE": PURPLE,
    "PINK": PINK,
    "TEAL": TEAL,
}}


def resolve_color(value):

    if not value:
        return WHITE

    return COLOR_MAP.get(
        value.upper(),
        WHITE,
    )


def apply_position(
    mobject,
    position,
):

    if position is None:
        return

    if isinstance(
        position,
        list,
    ):

        values = list(position)

        if len(values) == 2:
            values.append(0)

        mobject.move_to(
            np.array(
                values,
                dtype=float,
            )
        )

        return

    positions = {{
        "top": UP * 3.0,
        "bottom": DOWN * 3.0,
        "left": LEFT * 4.0,
        "right": RIGHT * 4.0,
        "center": ORIGIN,
    }}

    target = positions.get(
        position
    )

    if target is not None:
        mobject.move_to(
            target
        )


def build_object(spec):

    object_type = spec["type"]

    if object_type == "text":

        mob = Text(
            spec["content"],
            font_size=(
                spec["font_size"]
                or 48
            ),
            font=(
                spec["font"]
                or "DejaVu Serif"
            ),
            color=resolve_color(
                spec["color"]
            ),
        )

    elif object_type == "math":

        mob = MathTex(
            spec["content"],
            font_size=(
                spec["font_size"]
                or 48
            ),
            color=resolve_color(
                spec["color"]
            ),
        )

    elif object_type == "square":

        opacity = (
            spec["fill_opacity"]
            if spec["fill_opacity"]
            is not None
            else 0.65
        )

        mob = Square(
            side_length=1.8,
            fill_opacity=opacity,
            stroke_width=(
                spec["stroke_width"]
                if spec["stroke_width"]
                is not None
                else 2
            ),
        )

        mob.set_fill(
            color=resolve_color(
                spec["color"]
            ),
            opacity=opacity,
        )

    elif object_type == "circle":

        opacity = (
            spec["fill_opacity"]
            if spec["fill_opacity"]
            is not None
            else 0.65
        )

        mob = Circle(
            radius=1.25,
            fill_opacity=opacity,
            stroke_width=(
                spec["stroke_width"]
                if spec["stroke_width"]
                is not None
                else 2
            ),
        )

        mob.set_fill(
            color=resolve_color(
                spec["color"]
            ),
            opacity=opacity,
        )

    elif object_type == "triangle":

        opacity = (
            spec["fill_opacity"]
            if spec["fill_opacity"]
            is not None
            else 0.65
        )

        mob = Triangle(
            fill_opacity=opacity,
            stroke_width=(
                spec["stroke_width"]
                if spec["stroke_width"]
                is not None
                else 2
            ),
        )

        mob.set_fill(
            color=resolve_color(
                spec["color"]
            ),
            opacity=opacity,
        )

    else:
        raise ValueError(
            f"Unsupported object type: {{object_type}}"
        )

    if spec["scale"] is not None:
        mob.scale(
            spec["scale"]
        )

    apply_position(
        mob,
        spec["position"],
    )

    return mob


def resolve_targets(
    objects,
    operation,
):

    names = []

    if operation["target"]:
        names.append(
            operation["target"]
        )

    names.extend(
        operation["targets"]
    )

    return [
        objects[name]
        for name in names
        if name in objects
    ]


def play_operation(
    scene,
    objects,
    operation,
    state,
):

    operation_type = operation["type"]

    duration = (
        operation["duration"]
        or 1.0
    )

    target_objects = resolve_targets(
        objects,
        operation,
    )

    if operation_type == "write":

        if operation["target"]:

            mob = objects[
                operation["target"]
            ]

            scene.play(
                Write(mob),
                run_time=duration,
            )

            state["last_mobject"] = mob

            return

        expression = (
            operation["expression"]
        )

        if not expression:
            raise ValueError(
                "Write operation requires "
                "target or expression."
            )

        mob = MathTex(
            expression,
            font_size=48,
        )

        mob.move_to(
            ORIGIN
        )

        scene.play(
            Write(mob),
            run_time=duration,
        )

        state["last_mobject"] = mob

        return

    if operation_type == "grow":

        animations = [
            GrowFromCenter(mob)
            for mob in target_objects
        ]

        if not animations:
            raise ValueError(
                "Grow requires valid targets."
            )

        scene.play(
            *animations,
            lag_ratio=(
                operation["lag_ratio"]
                if operation["lag_ratio"]
                is not None
                else 0.15
            ),
            run_time=duration,
        )

        return

    if operation_type == "fade_in":

        animations = [
            FadeIn(
                mob,
                shift=UP * 0.25,
            )
            for mob in target_objects
        ]

        if not animations:
            raise ValueError(
                "FadeIn requires valid targets."
            )

        scene.play(
            *animations,
            run_time=duration,
        )

        return

    if operation_type in {
        "fade",
        "fade_out",
    }:

        animations = [
            FadeOut(mob)
            for mob in target_objects
        ]

        if not animations:
            raise ValueError(
                "FadeOut requires valid targets."
            )

        scene.play(
            *animations,
            run_time=duration,
        )

        return

    if operation_type == "indicate":

        animations = [
            Indicate(
                mob,
                scale_factor=(
                    operation["scale_factor"]
                    or 1.12
                ),
            )
            for mob in target_objects
        ]

        if not animations:
            raise ValueError(
                "Indicate requires valid targets."
            )

        scene.play(
            *animations,
            run_time=duration,
        )

        return

    if operation_type == "highlight":

        if not target_objects:
            raise ValueError(
                "Highlight requires valid target."
            )

        rectangles = [
            SurroundingRectangle(
                mob,
                buff=0.12,
                corner_radius=0.08,
            )
            for mob in target_objects
        ]

        for rectangle in rectangles:
            scene.play(
                Create(rectangle),
                run_time=duration,
            )

        return

    if operation_type == "transform":

        if operation["target"]:

            source = objects[
                operation["target"]
            ]

            expression = (
                operation["to_expression"]
            )

            if not expression:
                raise ValueError(
                    "Transform requires "
                    "to_expression."
                )

            target = MathTex(
                expression,
                font_size=48,
            )

            target.move_to(
                source.get_center()
            )

            scene.play(
                Transform(
                    source,
                    target,
                ),
                run_time=duration,
            )

            return

        source_expression = (
            operation["from_expression"]
        )

        target_expression = (
            operation["to_expression"]
        )

        if not target_expression:
            raise ValueError(
                "Transform requires "
                "to_expression."
            )

        source = state.get(
            "last_mobject"
        )

        if source is None:

            if not source_expression:
                raise ValueError(
                    "Legacy transform requires "
                    "from_expression."
                )

            source = MathTex(
                source_expression,
                font_size=48,
            )

            source.move_to(
                ORIGIN
            )

            scene.add(
                source
            )

        target = MathTex(
            target_expression,
            font_size=48,
        )

        target.move_to(
            source.get_center()
        )

        scene.play(
            Transform(
                source,
                target,
            ),
            run_time=duration,
        )

        state["last_mobject"] = source

        return

    if operation_type == "wait":

        scene.wait(
            duration
        )

        return

    raise ValueError(
        f"Unsupported operation: {{operation_type}}"
    )


class GeneratedScene(Scene):

    def construct(self):

        objects = {{}}

        state = {{
            "last_mobject": None,
        }}

        for object_spec in (
            SCENE_DATA["objects"]
        ):

            object_id = object_spec["id"]

            objects[object_id] = (
                build_object(
                    object_spec
                )
            )

        for object_id, mob in objects.items():

            object_type = next(
                (
                    item["type"]
                    for item
                    in SCENE_DATA["objects"]
                    if item["id"]
                    == object_id
                ),
                None,
            )

            if object_type in {{
                "text",
                "math",
            }}:
                mob.set_opacity(
                    0
                )

        for operation in (
            SCENE_DATA["operations"]
        ):

            play_operation(
                self,
                objects,
                operation,
                state,
            )

        self.wait(
            0.2
        )
'''
