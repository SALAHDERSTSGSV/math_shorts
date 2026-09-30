from pathlib import Path

from audio.piper import PiperAudioGenerator


def test_piper_generates_audio(tmp_path: Path) -> None:
    output = tmp_path / "voice.wav"

    generator = PiperAudioGenerator()

    artifact = generator.generate(
        "Let's solve this equation step by step.",
        output,
    )

    assert output.is_file()
    assert output.stat().st_size > 0
    assert artifact.path == str(output)
