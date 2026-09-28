from __future__ import annotations

from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class AnimationActionType(str, Enum):
    WRITE = "write"
    TRANSFORM = "transform"
    HIGHLIGHT = "highlight"
    FADE = "fade"
    WAIT = "wait"

    GROW = "grow"
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    INDICATE = "indicate"


class SceneObjectType(str, Enum):
    TEXT = "text"
    MATH = "math"

    SQUARE = "square"
    CIRCLE = "circle"
    TRIANGLE = "triangle"


class ScenePosition(str, Enum):
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"


class SceneObject(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    id: str = Field(
        min_length=1,
        max_length=100,
    )

    type: SceneObjectType

    content: str | None = Field(
        default=None,
        max_length=2000,
    )

    position: ScenePosition | list[float] | None = None

    font_size: float | None = Field(
        default=None,
        gt=0,
        le=300,
    )

    font: str | None = Field(
        default=None,
        max_length=200,
    )

    color: str | None = Field(
        default=None,
        max_length=50,
    )

    fill_opacity: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    stroke_width: float | None = Field(
        default=None,
        ge=0,
        le=20,
    )

    scale: float | None = Field(
        default=None,
        gt=0,
        le=10,
    )

    @field_validator(
        "id",
        "content",
        "font",
        "color",
    )
    @classmethod
    def text_not_empty(
        cls,
        value: str | None,
    ) -> str | None:

        if value is not None and not value.strip():
            raise ValueError(
                "text fields cannot be empty"
            )

        return value

    @field_validator("position")
    @classmethod
    def validate_position(
        cls,
        value,
    ):
        if isinstance(value, list):
            if len(value) not in (2, 3):
                raise ValueError(
                    "Custom position must contain 2 or 3 numbers."
                )

        return value

    @model_validator(mode="after")
    def validate_object(self) -> "SceneObject":

        content_required = {
            SceneObjectType.TEXT,
            SceneObjectType.MATH,
        }

        if self.type in content_required:
            if not self.content:
                raise ValueError(
                    f"{self.type.value} object requires content."
                )

        return self


class AnimationAction(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    action: AnimationActionType

    # Legacy expression-based API.
    expression: str | None = None

    from_expression: str | None = Field(
        default=None,
        alias="from",
    )

    to_expression: str | None = Field(
        default=None,
        alias="to",
    )

    # New scene-based API.
    target: str | None = None

    targets: list[str] | None = None

    duration: float | None = Field(
        default=None,
        gt=0,
    )

    lag_ratio: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    scale_factor: float | None = Field(
        default=None,
        gt=0,
        le=5,
    )

    @field_validator(
        "expression",
        "from_expression",
        "to_expression",
        "target",
    )
    @classmethod
    def text_not_empty(
        cls,
        value: str | None,
    ) -> str | None:

        if value is not None and not value.strip():
            raise ValueError(
                "text fields cannot be empty"
            )

        return value

    @field_validator("targets")
    @classmethod
    def targets_not_empty(
        cls,
        value: list[str] | None,
    ) -> list[str] | None:

        if value is not None:
            if not value:
                raise ValueError(
                    "targets cannot be empty."
                )

            if any(
                not target.strip()
                for target in value
            ):
                raise ValueError(
                    "targets cannot contain empty values."
                )

        return value

    @model_validator(mode="after")
    def validate_action(self) -> "AnimationAction":

        if self.action == AnimationActionType.WRITE:

            if not self.expression and not self.target:
                raise ValueError(
                    "write action requires expression or target."
                )

        elif self.action == AnimationActionType.TRANSFORM:

            legacy_transform = (
                self.from_expression
                and self.to_expression
            )

            object_transform = (
                self.target
                and self.to_expression
            )

            if not legacy_transform and not object_transform:
                raise ValueError(
                    "transform action requires "
                    "'from' + 'to', or target + 'to'."
                )

        elif self.action in {
            AnimationActionType.HIGHLIGHT,
            AnimationActionType.FADE,
            AnimationActionType.FADE_IN,
            AnimationActionType.FADE_OUT,
            AnimationActionType.GROW,
            AnimationActionType.INDICATE,
        }:

            if not self.target and not self.targets:
                raise ValueError(
                    f"{self.action.value} action requires "
                    "target or targets."
                )

        elif self.action == AnimationActionType.WAIT:

            if self.duration is None:
                raise ValueError(
                    "wait action requires duration."
                )

        return self


class AnimationSpec(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    # Legacy format.
    actions: list[AnimationAction] = Field(
        default_factory=list,
        max_length=100,
    )

    # Rich scene format.
    objects: list[SceneObject] = Field(
        default_factory=list,
        max_length=100,
    )

    animations: list[AnimationAction] = Field(
        default_factory=list,
        max_length=200,
    )

    @model_validator(mode="after")
    def validate_spec(self) -> "AnimationSpec":

        if not self.actions and not self.animations:
            raise ValueError(
                "AnimationSpec requires actions or animations."
            )

        return self


class GeneratedContentSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    topic: str = Field(
        min_length=1,
        max_length=200,
    )

    difficulty: Difficulty

    problem: str = Field(
        min_length=1,
        max_length=1000,
    )

    solution_steps: list[str] = Field(
        min_length=1,
        max_length=30,
    )

    voice_script: str = Field(
        min_length=1,
        max_length=3000,
    )

    animation_spec: AnimationSpec

    @field_validator(
        "topic",
        "problem",
        "voice_script",
    )
    @classmethod
    def text_not_empty(
        cls,
        value: str,
    ) -> str:

        if not value.strip():
            raise ValueError(
                "text fields cannot be empty"
            )

        return value

    @field_validator("solution_steps")
    @classmethod
    def steps_not_empty(
        cls,
        steps: list[str],
    ) -> list[str]:

        if any(
            not step.strip()
            for step in steps
        ):
            raise ValueError(
                "solution steps cannot be empty"
            )

        return steps
