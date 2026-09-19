"""Persistent audit logging for ULTRON CODE decisions."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .safety import SafetyDecision


@dataclass(frozen=True)
class AuditEvent:
    """A serializable record of an action decision."""

    event_id: str
    action: str
    risk: str
    allowed: bool
    reason: str
    timestamp: str
    status: str
    correlation_id: str


class AuditLogger:
    """Append audit events to a JSON Lines file."""

    def __init__(self, path: Path | str = ".ultron/audit.jsonl") -> None:
        self.path = Path(path)

    def record(
        self,
        decision: SafetyDecision,
        status: str = "evaluated",
        correlation_id: str | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=str(uuid4()),
            action=decision.action,
            risk=decision.risk.value,
            allowed=decision.allowed,
            reason=decision.reason,
            timestamp=decision.timestamp,
            status=status,
            correlation_id=correlation_id or str(uuid4()),
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event), sort_keys=True) + "\n")
        return event

    def read_all(self) -> list[AuditEvent]:
        if not self.path.exists():
            return []
        events: list[AuditEvent] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(AuditEvent(**json.loads(line)))
        return events
