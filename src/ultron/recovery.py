"""Recovery helpers for restarting ULTRON workflow sessions."""

from dataclasses import dataclass

from .control import ControlState
from .run_store import RunStore


@dataclass(frozen=True)
class RecoveryState:
    """Minimal resumable runtime state."""

    can_resume: bool
    last_run_id: str | None
    reason: str


class RecoveryManager:
    """Determine whether an interrupted run may be resumed."""

    def __init__(self, run_store: RunStore) -> None:
        self.run_store = run_store

    def inspect(self, controls: ControlState) -> RecoveryState:
        latest = self.run_store.latest()
        if controls.emergency_stop:
            return RecoveryState(False, latest.get("run_id") if latest else None, "Emergency stop is active.")
        if controls.paused:
            return RecoveryState(False, latest.get("run_id") if latest else None, "Runtime is paused.")
        if latest is None:
            return RecoveryState(False, None, "No previous workflow run exists.")
        return RecoveryState(True, str(latest.get("run_id")), "Previous workflow state is available.")
