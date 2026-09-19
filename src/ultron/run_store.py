"""Persistent workflow run storage for ULTRON CODE."""

from dataclasses import asdict
from pathlib import Path
import json

from .correlation import ProgressAssessment, ProgressState
from .decision import Decision, DecisionKind
from .executor import ExecutionResult
from .models import Phase
from .providers import ProviderKind, ProviderSnapshot
from .synthesis import PromptProposal
from .workflow import WorkflowRun, WorkflowStage
from .workspace import WorkspaceSnapshot


class RunStore:
    """Persist and rehydrate workflow run snapshots as JSON documents."""

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

    def get(self, run_id: str) -> WorkflowRun:
        """Rehydrate a persisted workflow run by its run ID."""
        for payload in self.all():
            if payload.get("run_id") == run_id:
                return self._deserialize(payload)
        raise KeyError(f"Workflow run not found: {run_id}")

    def latest_typed(self) -> WorkflowRun | None:
        """Rehydrate the latest persisted run."""
        latest = self.latest()
        return self._deserialize(latest) if latest is not None else None

    @staticmethod
    def _serialize(run: WorkflowRun) -> dict[str, object]:
        payload = asdict(run)
        payload["stage"] = run.stage.value
        payload["provider"]["provider"] = run.provider.provider.value
        payload["assessment"]["state"] = run.assessment.state.value
        payload["decision"]["kind"] = run.decision.kind.value
        payload["prompt"]["provider"] = run.prompt.provider.value
        payload["prompt"]["decision"] = run.prompt.decision.value
        if run.execution is not None:
            payload["execution"]["command"] = list(run.execution.command)
        return payload

    @staticmethod
    def _deserialize(payload: dict[str, object]) -> WorkflowRun:
        provider_data = payload["provider"]
        workspace_data = payload["workspace"]
        assessment_data = payload["assessment"]
        decision_data = payload["decision"]
        prompt_data = payload["prompt"]
        execution_data = payload.get("execution")

        if not isinstance(provider_data, dict):
            raise ValueError("Invalid provider payload.")
        if not isinstance(workspace_data, dict):
            raise ValueError("Invalid workspace payload.")
        if not isinstance(assessment_data, dict):
            raise ValueError("Invalid assessment payload.")
        if not isinstance(decision_data, dict):
            raise ValueError("Invalid decision payload.")
        if not isinstance(prompt_data, dict):
            raise ValueError("Invalid prompt payload.")

        execution = None
        if isinstance(execution_data, dict):
            command = execution_data.get("command", [])
            if not isinstance(command, list):
                raise ValueError("Invalid execution command payload.")
            execution = ExecutionResult(
                action=str(execution_data["action"]),
                command=tuple(str(item) for item in command),
                return_code=int(execution_data["return_code"]),
                stdout=str(execution_data["stdout"]),
                stderr=str(execution_data["stderr"]),
                timed_out=bool(execution_data["timed_out"]),
                correlation_id=str(execution_data["correlation_id"]),
            )

        return WorkflowRun(
            run_id=str(payload["run_id"]),
            started_at=str(payload["started_at"]),
            stage=WorkflowStage(str(payload["stage"])),
            provider=ProviderSnapshot(
                provider=ProviderKind(str(provider_data["provider"])),
                session_id=provider_data.get("session_id"),
                summary=str(provider_data["summary"]),
                progress=provider_data.get("progress"),
            ),
            workspace=WorkspaceSnapshot(
                root=str(workspace_data["root"]),
                branch=workspace_data.get("branch"),
                changed_files=tuple(str(item) for item in workspace_data.get("changed_files", ())),
                untracked_files=tuple(
                    str(item) for item in workspace_data.get("untracked_files", ())
                ),
                git_available=bool(workspace_data["git_available"]),
            ),
            assessment=ProgressAssessment(
                state=ProgressState(str(assessment_data["state"])),
                reason=str(assessment_data["reason"]),
                provider=str(assessment_data["provider"]),
                changed_file_count=int(assessment_data["changed_file_count"]),
                reported_progress=assessment_data.get("reported_progress"),
            ),
            decision=Decision(
                kind=DecisionKind(str(decision_data["kind"])),
                rationale=str(decision_data["rationale"]),
                requires_approval=bool(decision_data["requires_approval"]),
            ),
            prompt=PromptProposal(
                provider=ProviderKind(str(prompt_data["provider"])),
                prompt=str(prompt_data["prompt"]),
                reason=str(prompt_data["reason"]),
                decision=DecisionKind(str(prompt_data["decision"])),
                phase_id=prompt_data.get("phase_id"),
                requires_approval=bool(prompt_data["requires_approval"]),
            ),
            execution=execution,
            notes=tuple(str(item) for item in payload.get("notes", ())),
        )
