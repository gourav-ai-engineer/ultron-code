"""Human approval gateway for ULTRON CODE."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from uuid import uuid4
import json

from .safety import ActionRisk, SafetyDecision


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"


@dataclass(frozen=True)
class ApprovalRequest:
    """Persistent request awaiting an explicit human decision."""

    request_id: str
    action: str
    rationale: str
    risk: ActionRisk
    status: ApprovalStatus
    requested_at: str
    resolved_at: str | None = None
    resolution_note: str = ""
    correlation_id: str = ""


class ApprovalGateway:
    """Create and resolve approval requests without executing actions."""

    def __init__(self, path: Path | str = ".ultron/approvals.json") -> None:
        self.path = Path(path)

    def request(
        self,
        safety_decision: SafetyDecision,
        rationale: str,
        correlation_id: str | None = None,
    ) -> ApprovalRequest:
        """Create a pending request for an action that requires approval."""
        if safety_decision.risk != ActionRisk.REQUIRES_APPROVAL:
            raise ValueError("Approval requests are only valid for actions requiring approval.")

        request = ApprovalRequest(
            request_id=str(uuid4()),
            action=safety_decision.action,
            rationale=rationale,
            risk=safety_decision.risk,
            status=ApprovalStatus.PENDING,
            requested_at=datetime.now(timezone.utc).isoformat(),
            correlation_id=correlation_id or str(uuid4()),
        )
        requests = self._load()
        requests.append(request)
        self._save(requests)
        return request

    def resolve(
        self,
        request_id: str,
        status: ApprovalStatus,
        resolution_note: str = "",
    ) -> ApprovalRequest:
        """Resolve a pending request with an explicit human decision."""
        if status == ApprovalStatus.PENDING:
            raise ValueError("A request can only be resolved with a final approval status.")

        requests = self._load()
        for index, request in enumerate(requests):
            if request.request_id != request_id:
                continue
            if request.status != ApprovalStatus.PENDING:
                raise ValueError("Approval request has already been resolved.")

            resolved = ApprovalRequest(
                request_id=request.request_id,
                action=request.action,
                rationale=request.rationale,
                risk=request.risk,
                status=status,
                requested_at=request.requested_at,
                resolved_at=datetime.now(timezone.utc).isoformat(),
                resolution_note=resolution_note,
                correlation_id=request.correlation_id,
            )
            requests[index] = resolved
            self._save(requests)
            return resolved

        raise KeyError(f"Approval request not found: {request_id}")

    def pending(self) -> list[ApprovalRequest]:
        """Return unresolved approval requests."""
        return [item for item in self._load() if item.status == ApprovalStatus.PENDING]

    def get(self, request_id: str) -> ApprovalRequest:
        """Return one approval request by ID."""
        for request in self._load():
            if request.request_id == request_id:
                return request
        raise KeyError(f"Approval request not found: {request_id}")

    def _load(self) -> list[ApprovalRequest]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"Invalid approval store: {self.path}")
        return [
            ApprovalRequest(
                request_id=item["request_id"],
                action=item["action"],
                rationale=item["rationale"],
                risk=ActionRisk(item["risk"]),
                status=ApprovalStatus(item["status"]),
                requested_at=item["requested_at"],
                resolved_at=item.get("resolved_at"),
                resolution_note=item.get("resolution_note", ""),
                correlation_id=item.get("correlation_id", ""),
            )
            for item in payload
        ]

    def _save(self, requests: list[ApprovalRequest]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(request) for request in requests]
        for item in payload:
            item["risk"] = item["risk"].value
            item["status"] = item["status"].value
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
