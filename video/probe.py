from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


class VideoProbeError(Exception):
    """Raised when video metadata cannot be read."""


@dataclass(frozen=True)
class VideoMetadata:
    duration_seconds: float
    width: int
    height: int


class VideoProbe:
    """
    Reads authoritative metadata from a rendered video
    using ffprobe.

    We do not trust the renderer's expected dimensions or
    estimated duration. The actual MP4 is inspected.
    """

    def __init__(
        self,
        ffprobe_command: str = "ffprobe",
    ):
        self.ffprobe_command = ffprobe_command

    def probe(
        self,
        video_path: str | Path,
    ) -> VideoMetadata:

        path = Path(video_path)

        if not path.is_file():
            raise VideoProbeError(
                f"Video file does not exist: {path}"
            )

        if path.stat().st_size == 0:
            raise VideoProbeError(
                f"Video file is empty: {path}"
            )

        if shutil.which(self.ffprobe_command) is None:
            raise VideoProbeError(
                f"ffprobe executable not found: "
                f"{self.ffprobe_command}"
            )

        command = [
            self.ffprobe_command,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,duration",
            "-of",
            "json",
            str(path),
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )

        except OSError as exc:
            raise VideoProbeError(
                f"Failed to execute ffprobe: {exc}"
            ) from exc

        if result.returncode != 0:
            raise VideoProbeError(
                "ffprobe failed.\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )

        try:
            payload = json.loads(result.stdout)

            streams = payload.get("streams", [])

            if not streams:
                raise VideoProbeError(
                    "ffprobe returned no video stream."
                )

            stream = streams[0]

            width = int(stream["width"])
            height = int(stream["height"])
            duration = float(stream["duration"])

        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise VideoProbeError(
                "ffprobe returned invalid video metadata."
            ) from exc

        if width <= 0 or height <= 0:
            raise VideoProbeError(
                "Video dimensions must be greater than zero."
            )

        if duration <= 0:
            raise VideoProbeError(
                "Video duration must be greater than zero."
            )

        return VideoMetadata(
            duration_seconds=duration,
            width=width,
            height=height,
        )
