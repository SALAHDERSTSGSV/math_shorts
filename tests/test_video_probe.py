import json
from pathlib import Path

import pytest

from video.probe import (
    VideoMetadata,
    VideoProbe,
    VideoProbeError,
)


def test_probe_reads_video_metadata(
    tmp_path,
    monkeypatch,
):

    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake video")

    payload = {
        "streams": [
            {
                "width": 1080,
                "height": 1920,
                "duration": "4.25",
            }
        ]
    }

    class Result:
        returncode = 0
        stdout = json.dumps(payload)
        stderr = ""

    monkeypatch.setattr(
        "video.probe.shutil.which",
        lambda command: "/usr/bin/ffprobe",
    )

    monkeypatch.setattr(
        "video.probe.subprocess.run",
        lambda *args, **kwargs: Result(),
    )

    metadata = VideoProbe().probe(video)

    assert metadata == VideoMetadata(
        duration_seconds=4.25,
        width=1080,
        height=1920,
    )


def test_probe_rejects_missing_file(tmp_path):

    with pytest.raises(VideoProbeError):
        VideoProbe().probe(
            tmp_path / "missing.mp4"
        )


def test_probe_rejects_empty_file(tmp_path):

    video = tmp_path / "empty.mp4"
    video.touch()

    with pytest.raises(VideoProbeError):
        VideoProbe().probe(video)


def test_probe_rejects_missing_ffprobe(
    tmp_path,
    monkeypatch,
):

    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake")

    monkeypatch.setattr(
        "video.probe.shutil.which",
        lambda command: None,
    )

    with pytest.raises(VideoProbeError):
        VideoProbe().probe(video)


def test_probe_rejects_invalid_metadata(
    tmp_path,
    monkeypatch,
):

    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake")

    class Result:
        returncode = 0
        stdout = '{"streams":[]}'
        stderr = ""

    monkeypatch.setattr(
        "video.probe.shutil.which",
        lambda command: "/usr/bin/ffprobe",
    )

    monkeypatch.setattr(
        "video.probe.subprocess.run",
        lambda *args, **kwargs: Result(),
    )

    with pytest.raises(VideoProbeError):
        VideoProbe().probe(video)
