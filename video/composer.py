from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from domain.artifacts import AudioArtifact, ComposedVideo, RenderedVideo
from video.probe import VideoProbe


class VideoComposerError(Exception):
    """Raised when video composition fails."""


class FFmpegComposer:
    """Compose a vertical YouTube Short from hook, animation, and narration."""

    def __init__(
        self,
        ffmpeg_command: str = "ffmpeg",
        probe: VideoProbe | None = None,
        width: int = 1080,
        height: int = 1920,
    ) -> None:
        self.ffmpeg_command = ffmpeg_command
        self.probe = probe or VideoProbe()
        self.width = width
        self.height = height

    def _check_ffmpeg(self) -> None:
        if shutil.which(self.ffmpeg_command) is None:
            raise VideoComposerError(
                f"FFmpeg executable not found: {self.ffmpeg_command}"
            )

    def _validate_input_video(self, path: Path, name: str) -> None:
        try:
            metadata = self.probe.probe(path)
        except Exception as exc:
            raise VideoComposerError(
                f"Invalid {name} video: {path}"
            ) from exc

        if metadata.width != self.width or metadata.height != self.height:
            raise VideoComposerError(
                f"{name} must be {self.width}x{self.height}, "
                f"got {metadata.width}x{metadata.height}"
            )

    def _validate_audio(self, path: Path) -> None:
        if not path.is_file():
            raise VideoComposerError(
                f"Audio file does not exist: {path}"
            )

        if path.stat().st_size == 0:
            raise VideoComposerError(
                f"Audio file is empty: {path}"
            )

    def compose(
        self,
        hook: str | Path,
        animation: RenderedVideo,
        audio: AudioArtifact,
        output_path: str | Path,
    ) -> ComposedVideo:
        self._check_ffmpeg()

        hook_path = Path(hook)
        animation_path = Path(animation.path)
        audio_path = Path(audio.path)
        output = Path(output_path)

        output.parent.mkdir(parents=True, exist_ok=True)

        self._validate_input_video(hook_path, "hook")
        self._validate_input_video(animation_path, "animation")
        self._validate_audio(audio_path)

        if output.exists():
            output.unlink()

        command = [
            self.ffmpeg_command,
            "-y",

            # Hook video.
            "-i",
            str(hook_path),

            # Manim video.
            "-i",
            str(animation_path),

            # Piper narration.
            "-i",
            str(audio_path),

            "-filter_complex",
            (
                "[0:v]setpts=PTS-STARTPTS[hook];"
                "[1:v]setpts=PTS-STARTPTS[animation];"
                "[hook][animation]"
                "concat=n=2:v=1:a=0"
                "[video]"
            ),

            # Use the generated narration as the final audio.
            "-map",
            "[video]",
            "-map",
            "2:a:0",

            # YouTube-friendly encoding.
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",

            "-c:a",
            "aac",
            "-b:a",
            "192k",

            # Stop when the video ends.
            "-shortest",

            str(output),
        ]

        try:
            subprocess.run(
                command,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            raise VideoComposerError(
                "FFmpeg failed to compose the Short"
            ) from exc

        if not output.is_file() or output.stat().st_size == 0:
            raise VideoComposerError(
                f"FFmpeg did not create a valid output: {output}"
            )

        metadata = self.probe.probe(output)

        if metadata.width != self.width:
            raise VideoComposerError(
                f"Output width is {metadata.width}, "
                f"expected {self.width}"
            )

        if metadata.height != self.height:
            raise VideoComposerError(
                f"Output height is {metadata.height}, "
                f"expected {self.height}"
            )

        return ComposedVideo(
            path=str(output),
            duration_seconds=metadata.duration_seconds,
            width=metadata.width,
            height=metadata.height,
        )
