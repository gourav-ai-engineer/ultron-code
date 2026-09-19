"""Provider interaction gateway for ULTRON CODE."""

from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

from .approval import ApprovalRequest, ApprovalStatus
from .safety import ActionRisk


@dataclass(frozen=True)
class InteractionResult:
    """Result of a provider prompt submission."""

    interaction_id: str
    provider: str
    accepted: bool
    message: str
    correlation_id: str


class ProviderInteractionAdapter(Protocol):
    """Write-capable provider contract, separate from read-only snapshots."""

    @property
    def provider(self) -> str: ...

    def send_prompt(
        self,
        prompt: str,
        correlation_id: str,
        approval: ApprovalRequest | None = None,
        requires_approval: bool = True,
    ) -> InteractionResult: ...


class InteractionGateway:
    """Gate provider writes behind explicit approval."""

    def send(
        self,
        adapter: ProviderInteractionAdapter,
        prompt: str,
        approval: ApprovalRequest | None = None,
        requires_approval: bool = True,
        correlation_id: str | None = None,
    ) -> InteractionResult:
        workflow_id = correlation_id or str(uuid4())
        approved = approval is not None and approval.status == ApprovalStatus.APPROVED

        if requires_approval and not approved:
            return InteractionResult(
                interaction_id=str(uuid4()),
                provider=adapter.provider,
                accepted=False,
                message="Provider interaction requires explicit approval.",
                correlation_id=workflow_id,
            )

        if approval is not None and approval.risk == ActionRisk.BLOCKED:
            return InteractionResult(
                interaction_id=str(uuid4()),
                provider=adapter.provider,
                accepted=False,
                message="Blocked actions cannot be submitted.",
                correlation_id=workflow_id,
            )

        return adapter.send_prompt(
            prompt,
            workflow_id,
            approval=approval,
            requires_approval=requires_approval,
        )
