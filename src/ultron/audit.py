"""Persistent audit logging for ULTRON CODE decisions and execution attempts."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .safety import ActionRisk, SafetyDecision
from .security import redact_secrets


@dataclass(frozen=True)
class AuditEvent:
    """A serializable record of a decision or execution attempt."""

    event_id: str
    action: str
    risk: str
    allowed: bool
    reason: str
    timestamp: str
    status: str
    correlation_id: str
    return_code: int | None = None
    timed_out: bool = False
    error: str = ""


class AuditLogger:
    """Append audit events to a JSON Lines file."""

    def __init__(self, path: Path | str = ".ultron/audit.jsonl") -> None:
        self.path = Path(path)

    def record(
        self,
        decision: SafetyDecision,
        status: str = "evaluated",
        correlation_id: str | None = None,
        return_code: int | None = None,
        timed_out: bool = False,
        error: str = "",
    ) -> AuditEvent:
        """Record a safety decision and optional execution outcome."""
        event = AuditEvent(
            event_id=str(uuid4()),
            action=redact_secrets(decision.action),
            risk=decision.risk.value,
            allowed=decision.allowed,
            reason=redact_secrets(decision.reason),
            timestamp=decision.timestamp,
            status=status,
            correlation_id=correlation_id or str(uuid4()),
            return_code=return_code,
            timed_out=timed_out,
            error=redact_secrets(error),
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event), sort_keys=True) + "\n")
        return event

    def record_blocked(
        self,
        action: str,
        reason: str,
        correlation_id: str | None = None,
    ) -> AuditEvent:
        """Record an action rejected before normal safety evaluation."""
        decision = SafetyDecision(
            action=action,
            risk=ActionRisk.BLOCKED,
            allowed=False,
            reason=reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return self.record(decision, status="denied", correlation_id=correlation_id)

    def record_interaction(
        self,
        provider: str,
        status: str,
        correlation_id: str,
        accepted: bool,
    ) -> AuditEvent:
        """Record provider prompt-delivery metadata without storing prompt content."""
        decision = SafetyDecision(
            action=f"provider:{redact_secrets(provider)}:send_prompt",
            risk=ActionRisk.REQUIRES_APPROVAL,
            allowed=accepted,
            reason="Provider interaction accepted." if accepted else "Provider interaction denied.",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return self.record(
            decision,
            status=f"interaction_{status}",
            correlation_id=correlation_id,
        )

    def read_all(self) -> list[AuditEvent]:
        if not self.path.exists():
            return []
        events: list[AuditEvent] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(AuditEvent(**json.loads(line)))
        return events
