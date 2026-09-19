"""Controlled delivery of synthesized prompts to provider interaction adapters."""

from dataclasses import dataclass

from .approval import ApprovalRequest
from .audit import AuditLogger
from .interaction import InteractionResult, ProviderInteractionAdapter, InteractionGateway
from .security import redact_secrets
from .synthesis import PromptProposal
from .workflow import WorkflowRun


@dataclass(frozen=True)
class DeliveryResult:
    """Provider prompt delivery outcome."""

    run_id: str
    interaction: InteractionResult


class PromptDeliveryService:
    """Deliver a workflow prompt through an explicitly approved adapter."""

    def __init__(
        self,
        gateway: InteractionGateway | None = None,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self.gateway = gateway or InteractionGateway()
        self.audit_logger = audit_logger

    def deliver(
        self,
        run: WorkflowRun,
        adapter: ProviderInteractionAdapter,
        approval: ApprovalRequest | None = None,
    ) -> DeliveryResult:
        proposal: PromptProposal = run.prompt
        interaction = self.gateway.send(
            adapter,
            redact_secrets(proposal.prompt),
            approval=approval,
            requires_approval=proposal.requires_approval,
        )
        if self.audit_logger is not None:
            status = "sent" if interaction.accepted else "denied"
            self.audit_logger.record_interaction(
                provider=interaction.provider,
                status=status,
                correlation_id=run.run_id,
                accepted=interaction.accepted,
            )
        return DeliveryResult(run_id=run.run_id, interaction=interaction)
