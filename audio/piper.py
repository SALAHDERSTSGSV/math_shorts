from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from domain.artifacts import AudioArtifact


class PiperError(Exception):
    """Raised when Piper cannot generate the audio."""


class PiperAudioGenerator:
    """Generate speech audio using the local Piper executable."""

    def __init__(
        self,
        model: str = "en_US-lessac-medium.onnx",
        piper_command: str = "piper",
    ) -> None:
        self.model = model
        self.piper_command = piper_command

    def generate(
        self,
        text: str,
        output_path: str | Path,
    ) -> AudioArtifact:
        if not text.strip():
            raise PiperError("Cannot generate audio from empty text")

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        if shutil.which(self.piper_command) is None:
            raise PiperError(
                f"Piper executable not found: {self.piper_command}"
            )

        try:
            subprocess.run(
                [
                    self.piper_command,
                    "--model",
                    self.model,
                    "--output_file",
                    str(output),
                ],
                input=text.encode("utf-8"),
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            raise PiperError("Piper failed to generate audio") from exc

        if not output.is_file() or output.stat().st_size == 0:
            raise PiperError(
                f"Piper did not create a valid audio file: {output}"
            )

        return AudioArtifact(
            path=str(output),
            duration_seconds=0.0,
            sample_rate=0,
        )
