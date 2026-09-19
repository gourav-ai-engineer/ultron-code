"""Persistent local state storage for ULTRON CODE."""

import json
from pathlib import Path

from .models import Project


class ProjectStateStore:
    """Read and write project state as JSON."""

    def __init__(self, path: Path | str = ".ultron/project.json") -> None:
        self.path = Path(path)

    def save(self, project: Project) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            project.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def load(self) -> Project:
        if not self.path.exists():
            raise FileNotFoundError(f"Project state not found: {self.path}")
        return Project.model_validate_json(self.path.read_text(encoding="utf-8"))
