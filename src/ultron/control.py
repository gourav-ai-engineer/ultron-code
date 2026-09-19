"""Persistent runtime controls for pausing and stopping ULTRON CODE."""

from dataclasses import asdict, dataclass
from pathlib import Path
import json


@dataclass(frozen=True)
class ControlState:
    """Runtime stop/pause state."""

    emergency_stop: bool = False
    paused: bool = False
    reason: str = ""


class ControlStore:
    """Persist operator controls locally."""

    def __init__(self, path: Path | str = ".ultron/control.json") -> None:
        self.path = Path(path)

    def get(self) -> ControlState:
        if not self.path.exists():
            return ControlState()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Invalid control state: {self.path}")
        return ControlState(
            emergency_stop=bool(payload.get("emergency_stop", False)),
            paused=bool(payload.get("paused", False)),
            reason=str(payload.get("reason", "")),
        )

    def set(
        self,
        *,
        emergency_stop: bool | None = None,
        paused: bool | None = None,
        reason: str | None = None,
    ) -> ControlState:
        current = self.get()
        state = ControlState(
            emergency_stop=current.emergency_stop if emergency_stop is None else emergency_stop,
            paused=current.paused if paused is None else paused,
            reason=current.reason if reason is None else reason,
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(asdict(state), indent=2),
            encoding="utf-8",
        )
        return state
