from pathlib import Path

import pytest

from audio.piper import PiperAudioGenerator
from domain.artifacts import RenderedVideo
from video.composer import FFmpegComposer, VideoComposerError


@pytest.mark.integration
def test_composer_creates_vertical_short(
    tmp_path: Path,
) -> None:
    hook = tmp_path / "hook.mp4"
    animation = tmp_path / "animation.mp4"
    audio = tmp_path / "voice.wav"
    output = tmp_path / "final_short.mp4"

    # Create a real vertical hook.
    import subprocess

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=1080x1920:d=1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(hook),
        ],
        check=True,
    )

    # Create a real vertical animation placeholder.
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=white:s=1080x1920:d=2",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(animation),
        ],
        check=True,
    )

    # Generate real Piper narration.
    generator = PiperAudioGenerator()

    audio_artifact = generator.generate(
        "Let's solve this equation step by step.",
        audio,
    )

    rendered_video = RenderedVideo(
        path=str(animation),
        duration_seconds=2.0,
        width=1080,
        height=1920,
    )

    composer = FFmpegComposer()

    result = composer.compose(
        hook=hook,
        animation=rendered_video,
        audio=audio_artifact,
        output_path=output,
    )

    assert output.is_file()
    assert output.stat().st_size > 0

    assert result.path == str(output)
    assert result.width == 1080
    assert result.height == 1920
    assert result.duration_seconds > 0
