from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass(frozen=True)
class AnimationSpec:
    objects: tuple[dict, ...] = ()
    animations: tuple[dict, ...] = ()
    actions: tuple[dict, ...] = ()
    duration_seconds: float | None = None


@dataclass(frozen=True)
class GeneratedContent:
    topic: str
    difficulty: Difficulty
    problem: str
    solution_steps: tuple[str, ...]
    voice_script: str
    animation_spec: dict
    generated_at: datetime = field(
        default_factory=utc_now
    )


@dataclass(frozen=True)
class MathVerificationResult:
    valid: bool
    problem: str
    verified_solution: str
    checks: tuple[str, ...]
    error: str | None = None
    verified_at: datetime = field(
        default_factory=utc_now
    )


@dataclass(frozen=True)
class RenderedVideo:
    path: str
    duration_seconds: float
    width: int
    height: int
    rendered_at: datetime = field(
        default_factory=utc_now
    )


@dataclass(frozen=True)
class AudioArtifact:
    path: str
    duration_seconds: float
    sample_rate: int
    generated_at: datetime = field(
        default_factory=utc_now
    )


@dataclass(frozen=True)
class ComposedVideo:
    path: str
    duration_seconds: float
    width: int
    height: int
    composed_at: datetime = field(
        default_factory=utc_now
    )


@dataclass(frozen=True)
class QCResult:
    passed: bool
    checks: tuple[str, ...]
    errors: tuple[str, ...] = ()
    checked_at: datetime = field(
        default_factory=utc_now
    )
