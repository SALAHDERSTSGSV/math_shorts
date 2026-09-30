from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from domain.artifacts import ComposedVideo, QCResult
from video.probe import VideoProbe


class QualityControlError(Exception):
    """Raised when quality-control inspection cannot be completed."""


class VideoQualityController:
    """Validate the final YouTube Short before it is marked complete."""

    def __init__(
        self,
        ffprobe_command: str = "ffprobe",
        probe: VideoProbe | None = None,
        width: int = 1080,
        height: int = 1920,
    ) -> None:
        self.ffprobe_command = ffprobe_command
        self.probe = probe or VideoProbe()
        self.width = width
        self.height = height

    def _check_ffprobe(self) -> None:
        if shutil.which(self.ffprobe_command) is None:
            raise QualityControlError(
                f"ffprobe executable not found: {self.ffprobe_command}"
            )

    def _check_audio_stream(self, path: Path) -> bool:
        try:
            result = subprocess.run(
                [
                    self.ffprobe_command,
                    "-v",
                    "error",
                    "-select_streams",
                    "a:0",
                    "-show_entries",
                    "stream=index",
                    "-of",
                    "csv=p=0",
                    str(path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            raise QualityControlError(
                f"Could not inspect audio stream: {path}"
            ) from exc

        return bool(result.stdout.strip())

    def check(self, video: ComposedVideo) -> QCResult:
        self._check_ffprobe()

        path = Path(video.path)

        checks: list[str] = []
        errors: list[str] = []

        # 1. File exists.
        if not path.is_file():
            errors.append(f"Output file does not exist: {path}")
        else:
            checks.append("output file exists")

            # 2. File is not empty.
            if path.stat().st_size == 0:
                errors.append("Output file is empty")
            else:
                checks.append("output file is non-empty")

        if errors:
            return QCResult(
                passed=False,
                checks=tuple(checks),
                errors=tuple(errors),
            )

        # 3. Probe video.
        try:
            metadata = self.probe.probe(path)
        except Exception as exc:
            errors.append(f"Video cannot be probed: {exc}")
            return QCResult(
                passed=False,
                checks=tuple(checks),
                errors=tuple(errors),
            )

        checks.append("video stream is readable")

        # 4. Resolution.
        if metadata.width != self.width:
            errors.append(
                f"Invalid width: {metadata.width}, "
                f"expected {self.width}"
            )
        else:
            checks.append("width is 1080")

        if metadata.height != self.height:
            errors.append(
                f"Invalid height: {metadata.height}, "
                f"expected {self.height}"
            )
        else:
            checks.append("height is 1920")

        # 5. Duration.
        if metadata.duration_seconds <= 0:
            errors.append("Video duration must be greater than zero")
        else:
            checks.append("duration is greater than zero")

        # 6. Audio stream.
        try:
            has_audio = self._check_audio_stream(path)
        except QualityControlError as exc:
            errors.append(str(exc))
        else:
            if has_audio:
                checks.append("audio stream exists")
            else:
                errors.append("No audio stream found")

        return QCResult(
            passed=not errors,
            checks=tuple(checks),
            errors=tuple(errors),
        )
