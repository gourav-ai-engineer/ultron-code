"""Persistent workflow run storage for ULTRON CODE."""

from dataclasses import asdict
from pathlib import Path
import json

from .workflow import WorkflowRun


class RunStore:
    """Persist workflow run snapshots as JSON documents."""

    def __init__(self, path: Path | str = ".ultron/runs.jsonl") -> None:
        self.path = Path(path)

    def append(self, run: WorkflowRun) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._serialize(run)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def all(self) -> list[dict[str, object]]:
        if not self.path.exists():
            return []
        runs: list[dict[str, object]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                if isinstance(item, dict):
                    runs.append(item)
        return runs

    def latest(self) -> dict[str, object] | None:
        runs = self.all()
        return runs[-1] if runs else None

    @staticmethod
    def _serialize(run: WorkflowRun) -> dict[str, object]:
        payload = asdict(run)
        payload["stage"] = run.stage.value
        payload["provider"]["provider"] = run.provider.provider.value
        payload["assessment"]["state"] = run.assessment.state.value
        payload["decision"]["kind"] = run.decision.kind.value
        if run.execution is not None:
            payload["execution"]["command"] = list(run.execution.command)
        return payload
