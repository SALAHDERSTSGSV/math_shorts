from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ai.schemas import (
    AnimationAction,
    AnimationActionType,
    AnimationSpec,
    SceneObject,
    SceneObjectType,
)


class AnimationValidationError(ValueError):
    """Raised when an animation DSL is invalid."""


class RenderObjectType(str, Enum):
    TEXT = "text"
    MATH = "math"

    SQUARE = "square"
    CIRCLE = "circle"
    TRIANGLE = "triangle"


@dataclass(frozen=True)
class SceneObjectDefinition:
    id: str
    type: RenderObjectType
    content: str | None = None
    position: str | tuple[float, ...] | None = None
    font_size: float | None = None
    font: str | None = None
    color: str | None = None
    fill_opacity: float | None = None
    stroke_width: float | None = None
    scale: float | None = None


class RenderOperationType(str, Enum):
    WRITE = "write"
    TRANSFORM = "transform"
    HIGHLIGHT = "highlight"
    FADE = "fade"
    WAIT = "wait"

    GROW = "grow"
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    INDICATE = "indicate"


@dataclass(frozen=True)
class RenderOperation:
    type: RenderOperationType

    expression: str | None = None

    from_expression: str | None = None
    to_expression: str | None = None

    target: str | None = None
    targets: tuple[str, ...] = ()

    duration: float | None = None
    lag_ratio: float | None = None
    scale_factor: float | None = None


class AnimationDSL:
    """
    Converts the AI animation contract into renderer-neutral
    scene objects and animation operations.

    Gemini never produces Python or Manim code.
    """

    def compile_objects(
        self,
        spec: AnimationSpec,
    ) -> tuple[SceneObjectDefinition, ...]:

        definitions: list[SceneObjectDefinition] = []

        seen_ids: set[str] = set()

        for obj in spec.objects:

            if obj.id in seen_ids:
                raise AnimationValidationError(
                    f"Duplicate scene object id: {obj.id}"
                )

            seen_ids.add(obj.id)

            definitions.append(
                self._compile_object(obj)
            )

        return tuple(definitions)

    def compile(
        self,
        spec: AnimationSpec,
    ) -> tuple[RenderOperation, ...]:

        actions = (
            spec.animations
            if spec.animations
            else spec.actions
        )

        operations: list[RenderOperation] = []

        for action in actions:
            operations.append(
                self._compile_action(action)
            )

        if not operations:
            raise AnimationValidationError(
                "Animation specification contains no operations."
            )

        return tuple(operations)

    def _compile_object(
        self,
        obj: SceneObject,
    ) -> SceneObjectDefinition:

        object_type = RenderObjectType(
            obj.type.value
        )

        position = obj.position

        if isinstance(position, list):
            position = tuple(
                float(value)
                for value in position
            )

        return SceneObjectDefinition(
            id=obj.id,
            type=object_type,
            content=obj.content,
            position=position,
            font_size=obj.font_size,
            font=obj.font,
            color=obj.color,
            fill_opacity=obj.fill_opacity,
            stroke_width=obj.stroke_width,
            scale=obj.scale,
        )

    def _compile_action(
        self,
        action: AnimationAction,
    ) -> RenderOperation:

        if action.action == AnimationActionType.WRITE:
            return self._compile_write(action)

        if action.action == AnimationActionType.TRANSFORM:
            return self._compile_transform(action)

        if action.action == AnimationActionType.HIGHLIGHT:
            return self._compile_highlight(action)

        if action.action == AnimationActionType.FADE:
            return self._compile_fade(action)

        if action.action == AnimationActionType.WAIT:
            return self._compile_wait(action)

        if action.action == AnimationActionType.GROW:
            return self._compile_grow(action)

        if action.action == AnimationActionType.FADE_IN:
            return self._compile_fade_in(action)

        if action.action == AnimationActionType.FADE_OUT:
            return self._compile_fade_out(action)

        if action.action == AnimationActionType.INDICATE:
            return self._compile_indicate(action)

        raise AnimationValidationError(
            f"Unsupported animation action: {action.action}"
        )

    def _compile_write(
        self,
        action: AnimationAction,
    ) -> RenderOperation:

        return RenderOperation(
            type=RenderOperationType.WRITE,
            expression=action.expression,
            target=action.target,
            duration=action.duration,
        )

    def _compile_transform(
        self,
        action: AnimationAction,
    ) -> RenderOperation:

        return RenderOperation(
            type=RenderOperationType.TRANSFORM,
            from_expression=action.from_expression,
            to_expression=action.to_expression,
            target=action.target,
            duration=action.duration,
        )

    def _compile_highlight(
        self,
        action: AnimationAction,
    ) -> RenderOperation:

        return RenderOperation(
            type=RenderOperationType.HIGHLIGHT,
            target=action.target,
            targets=tuple(action.targets or ()),
            duration=action.duration,
        )

    def _compile_fade(
        self,
        action: AnimationAction,
    ) -> RenderOperation:

        return RenderOperation(
            type=RenderOperationType.FADE,
            target=action.target,
            targets=tuple(action.targets or ()),
            duration=action.duration,
        )

    def _compile_wait(
        self,
        action: AnimationAction,
    ) -> RenderOperation:

        return RenderOperation(
            type=RenderOperationType.WAIT,
            duration=action.duration,
        )

    def _compile_grow(
        self,
        action: AnimationAction,
    ) -> RenderOperation:

        return RenderOperation(
            type=RenderOperationType.GROW,
            target=action.target,
            targets=tuple(action.targets or ()),
            duration=action.duration,
            lag_ratio=action.lag_ratio,
        )

    def _compile_fade_in(
        self,
        action: AnimationAction,
    ) -> RenderOperation:

        return RenderOperation(
            type=RenderOperationType.FADE_IN,
            target=action.target,
            targets=tuple(action.targets or ()),
            duration=action.duration,
        )

    def _compile_fade_out(
        self,
        action: AnimationAction,
    ) -> RenderOperation:

        return RenderOperation(
            type=RenderOperationType.FADE_OUT,
            target=action.target,
            targets=tuple(action.targets or ()),
            duration=action.duration,
        )

    def _compile_indicate(
        self,
        action: AnimationAction,
    ) -> RenderOperation:

        return RenderOperation(
            type=RenderOperationType.INDICATE,
            target=action.target,
            targets=tuple(action.targets or ()),
            duration=action.duration,
            scale_factor=action.scale_factor,
        )
