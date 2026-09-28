from domain.artifacts import (
    AnimationSpec,
    AudioArtifact,
    ComposedVideo,
    Difficulty,
    GeneratedContent,
    MathVerificationResult,
    QCResult,
    RenderedVideo,
)
from domain.stage_contracts import (
    AudioOutput,
    CompositionOutput,
    GenerationOutput,
    QCOutput,
    RenderingOutput,
    VerificationOutput,
)


def create_content():
    return GeneratedContent(
        topic="Exponents",
        difficulty=Difficulty.MEDIUM,
        problem="Solve 3x = x^9",
        solution_steps=(
            "Factor out x",
            "Solve x(3-x^8)=0",
            "Check the real solutions",
        ),
        voice_script="First, factor out x.",
        animation_spec={
            "actions": [
                {
                    "action": "write",
                    "expression": "3x = x^9",
                },
            ]
        },
    )


def create_pipeline_outputs():
    content = create_content()

    verification = MathVerificationResult(
        valid=True,
        problem=content.problem,
        verified_solution=(
            "x = 0, x = 3^(1/8), x = -3^(1/8)"
        ),
        checks=(
            "symbolic_equivalence",
            "solution_check",
        ),
    )

    animation = AnimationSpec(
        actions=tuple(
            content.animation_spec["actions"]
        ),
        duration_seconds=5.0,
    )

    video = RenderedVideo(
        path="runtime/rendered/job-001.mp4",
        duration_seconds=5.0,
        width=1080,
        height=1920,
    )

    audio = AudioArtifact(
        path="runtime/audio/job-001.wav",
        duration_seconds=5.2,
        sample_rate=48000,
    )

    composed = ComposedVideo(
        path="runtime/final/job-001.mp4",
        duration_seconds=7.5,
        width=1080,
        height=1920,
    )

    qc = QCResult(
        passed=True,
        checks=(
            "resolution",
            "duration",
            "audio",
            "video",
        ),
    )

    return (
        content,
        verification,
        animation,
        video,
        audio,
        composed,
        qc,
    )


def test_generation_output_contains_generated_content():
    content = create_content()

    output = GenerationOutput(content)

    assert output.content.problem == "Solve 3x = x^9"


def test_stage_contracts_carry_pipeline_artifacts():
    (
        content,
        verification,
        animation,
        video,
        audio,
        composed,
        qc,
    ) = create_pipeline_outputs()

    verified = VerificationOutput(
        content,
        verification,
    )

    rendered = RenderingOutput(
        content,
        verification,
        animation,
        video,
    )

    voiced = AudioOutput(
        content,
        verification,
        animation,
        video,
        audio,
    )

    composed_output = CompositionOutput(
        content,
        verification,
        animation,
        video,
        audio,
        composed,
    )

    final = QCOutput(
        content,
        verification,
        animation,
        video,
        audio,
        composed,
        qc,
    )

    assert verified.verification.valid is True
    assert rendered.video.width == 1080
    assert voiced.audio.sample_rate == 48000
    assert composed_output.composed_video.height == 1920
    assert final.qc.passed is True
