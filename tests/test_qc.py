from pathlib import Path
import subprocess

from domain.artifacts import ComposedVideo
from video.qc import VideoQualityController


def create_test_video(path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=1080x1920:d=2",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=2",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            str(path),
        ],
        check=True,
        capture_output=True,
    )


def test_qc_accepts_valid_vertical_video(tmp_path: Path) -> None:
    video_path = tmp_path / "final_short.mp4"

    create_test_video(video_path)

    composed = ComposedVideo(
        path=str(video_path),
        duration_seconds=2.0,
        width=1080,
        height=1920,
    )

    qc = VideoQualityController()

    result = qc.check(composed)

    assert result.passed is True
    assert result.errors == ()

    assert "output file exists" in result.checks
    assert "video stream is readable" in result.checks
    assert "width is 1080" in result.checks
    assert "height is 1920" in result.checks
    assert "duration is greater than zero" in result.checks
    assert "audio stream exists" in result.checks


def test_qc_rejects_missing_video(tmp_path: Path) -> None:
    video_path = tmp_path / "missing.mp4"

    composed = ComposedVideo(
        path=str(video_path),
        duration_seconds=0.0,
        width=1080,
        height=1920,
    )

    qc = VideoQualityController()

    result = qc.check(composed)

    assert result.passed is False
    assert any(
        "does not exist" in error
        for error in result.errors
    )
