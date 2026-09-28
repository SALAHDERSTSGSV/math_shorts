from __future__ import annotations

from dataclasses import dataclass

from domain.artifacts import (
    AnimationSpec,
    AudioArtifact,
    ComposedVideo,
    GeneratedContent,
    MathVerificationResult,
    QCResult,
    RenderedVideo,
)


@dataclass(frozen=True)
class GenerationOutput:
    content: GeneratedContent


@dataclass(frozen=True)
class VerificationOutput:
    content: GeneratedContent
    verification: MathVerificationResult


@dataclass(frozen=True)
class RenderingOutput:
    content: GeneratedContent
    verification: MathVerificationResult
    animation: AnimationSpec
    video: RenderedVideo


@dataclass(frozen=True)
class AudioOutput:
    content: GeneratedContent
    verification: MathVerificationResult
    animation: AnimationSpec
    video: RenderedVideo
    audio: AudioArtifact


@dataclass(frozen=True)
class CompositionOutput:
    content: GeneratedContent
    verification: MathVerificationResult
    animation: AnimationSpec
    video: RenderedVideo
    audio: AudioArtifact
    composed_video: ComposedVideo


@dataclass(frozen=True)
class QCOutput:
    content: GeneratedContent
    verification: MathVerificationResult
    animation: AnimationSpec
    video: RenderedVideo
    audio: AudioArtifact
    composed_video: ComposedVideo
    qc: QCResult
