from __future__ import annotations

import json
from pathlib import Path


class HookSelectorError(Exception):
    """Raised when the hook selector cannot provide a valid hook."""


class HookSelector:
    """Selects hooks from a persistent round-robin pool."""

    def __init__(
        self,
        hooks_dir: str | Path = "media/hooks",
        state_path: str | Path = "runtime/hook_selector.json",
        hook_count: int = 10,
    ) -> None:
        if hook_count <= 0:
            raise ValueError("hook_count must be greater than zero")

        self.hooks_dir = Path(hooks_dir)
        self.state_path = Path(state_path)
        self.hook_count = hook_count

    def _hook_path(self, index: int) -> Path:
        return self.hooks_dir / f"hook_{index + 1:02d}.mp4"

    def _load_index(self) -> int:
        if not self.state_path.exists():
            return 0

        try:
            data = json.loads(self.state_path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise HookSelectorError(
                f"Cannot read hook selector state: {self.state_path}"
            ) from exc

        index = data.get("next_index", 0)

        if not isinstance(index, int):
            raise HookSelectorError("Invalid next_index in hook selector state")

        return index % self.hook_count

    def _save_index(self, index: int) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "next_index": index % self.hook_count,
        }

        temporary_path = self.state_path.with_suffix(".tmp")

        try:
            temporary_path.write_text(
                json.dumps(data, indent=2),
            )
            temporary_path.replace(self.state_path)
        except OSError as exc:
            raise HookSelectorError(
                f"Cannot save hook selector state: {self.state_path}"
            ) from exc

    def _validate_hooks(self) -> None:
        missing = [
            str(self._hook_path(index))
            for index in range(self.hook_count)
            if not self._hook_path(index).is_file()
        ]

        if missing:
            raise HookSelectorError(
                "Missing hook files:\n" + "\n".join(missing)
            )

    def select(self) -> Path:
        """Return the next hook and advance the round-robin index."""
        self._validate_hooks()

        index = self._load_index()
        hook_path = self._hook_path(index)

        next_index = (index + 1) % self.hook_count
        self._save_index(next_index)

        return hook_path

    def reset(self) -> None:
        """Reset selection so the next hook is hook_01.mp4."""
        self._save_index(0)
