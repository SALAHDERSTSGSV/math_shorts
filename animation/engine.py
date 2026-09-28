from __future__ import annotations

from dataclasses import dataclass

from ai.schemas import AnimationSpec
from animation.dsl import (
    AnimationDSL,
    RenderOperation,
    SceneObjectDefinition,
)


class AnimationEngineError(Exception):
    """Base exception for animation engine failures."""


@dataclass(frozen=True)
class CompiledAnimation:
    objects: tuple[SceneObjectDefinition, ...]
    operations: tuple[RenderOperation, ...]

    @property
    def operation_count(self) -> int:
        return len(self.operations)

    @property
    def object_count(self) -> int:
        return len(self.objects)

    @property
    def estimated_duration(self) -> float:
        return sum(
            operation.duration or 0.0
            for operation in self.operations
        )


class AnimationEngine:
    """
    Compiles AI animation specifications into a
    renderer-neutral scene representation.
    """

    def __init__(
        self,
        compiler: AnimationDSL | None = None,
    ):
        self.compiler = compiler or AnimationDSL()

    def compile(
        self,
        spec: AnimationSpec,
    ) -> CompiledAnimation:

        try:
            objects = self.compiler.compile_objects(
                spec
            )

            operations = self.compiler.compile(
                spec
            )

        except Exception as exc:
            raise AnimationEngineError(
                f"Animation compilation failed: {exc}"
            ) from exc

        if not operations:
            raise AnimationEngineError(
                "Animation compilation produced no operations."
            )

        return CompiledAnimation(
            objects=objects,
            operations=operations,
        )
