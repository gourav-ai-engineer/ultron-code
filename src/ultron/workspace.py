"""Read-only project workspace inspection utilities."""

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class WorkspaceSnapshot:
    """Safe snapshot of a local workspace."""

    root: str
    branch: str | None
    changed_files: tuple[str, ...]
    untracked_files: tuple[str, ...]
    git_available: bool


class WorkspaceObserver:
    """Inspect workspace metadata without modifying the workspace."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root).resolve()

    def snapshot(self) -> WorkspaceSnapshot:
        branch = self._git("branch", "--show-current")
        status = self._git("status", "--porcelain")
        entries = tuple(line for line in status.splitlines() if line.strip())
        changed: list[str] = []
        untracked: list[str] = []
        for entry in entries:
            path = entry[3:].strip() if len(entry) >= 4 else entry.strip()
            if entry.startswith("??"):
                untracked.append(path)
            else:
                changed.append(path)
        available = branch is not None or bool(entries)
        return WorkspaceSnapshot(
            root=str(self.root),
            branch=branch,
            changed_files=tuple(changed),
            untracked_files=tuple(untracked),
            git_available=available,
        )

    def _git(self, *args: str) -> str | None:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.root,
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        return result.stdout.strip()
