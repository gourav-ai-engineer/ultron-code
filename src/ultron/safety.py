"""Safety controls for ULTRON CODE actions."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


class ActionRisk(StrEnum):
    SAFE = "safe"
    REQUIRES_APPROVAL = "requires_approval"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class SafetyDecision:
    action: str
    risk: ActionRisk
    allowed: bool
    reason: str
    timestamp: str


@dataclass
class SafetyPolicy:
    """Evaluate actions without executing them."""

    dry_run: bool = True
    emergency_stop: bool = False
    blocked_tokens: set[str] = field(
        default_factory=lambda: {"rm -rf", "format", "del /s", "shutdown", "diskpart"}
    )
    approval_tokens: set[str] = field(
        default_factory=lambda: {"git push", "pip install", "npm install", "docker", "terraform"}
    )

    def evaluate(self, action: str, approved: bool = False) -> SafetyDecision:
        normalized = action.strip().lower()
        risk = ActionRisk.SAFE
        reason = "Action is permitted by the default policy."

        if self.emergency_stop:
            risk = ActionRisk.BLOCKED
            reason = "Emergency stop is enabled."
        elif any(token in normalized for token in self.blocked_tokens):
            risk = ActionRisk.BLOCKED
            reason = "Action matches a blocked destructive-operation pattern."
        elif any(token in normalized for token in self.approval_tokens):
            risk = ActionRisk.SAFE if approved else ActionRisk.REQUIRES_APPROVAL
            reason = "Explicit approval is required for this action." if not approved else "Approved action."

        allowed = risk == ActionRisk.SAFE and (not self.dry_run or approved or not self._needs_approval(normalized))
        if self.dry_run and risk == ActionRisk.SAFE:
            reason = "Dry-run mode: action evaluated but not executed."
            allowed = False

        return SafetyDecision(
            action=action,
            risk=risk,
            allowed=allowed,
            reason=reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _needs_approval(self, action: str) -> bool:
        return any(token in action for token in self.approval_tokens)
