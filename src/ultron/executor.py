"""Controlled local action execution for ULTRON CODE."""

from dataclasses import dataclass
from pathlib import Path
import shlex
import subprocess
from typing import Sequence
from uuid import uuid4

from .approval import ApprovalRequest, ApprovalStatus
from .audit import AuditLogger
from .safety import ActionRisk, SafetyPolicy


class ExecutionDeniedError(RuntimeError):
    """Raised when an action is outside the execution policy."""


@dataclass(frozen=True)
class ExecutionResult:
    """Result of a controlled command execution."""

    action: str
    command: tuple[str, ...]
    return_code: int
    stdout: str
    stderr: str
    timed_out: bool
    correlation_id: str


class ActionExecutor:
    """Execute only narrowly allowlisted commands inside one workspace."""

    DEFAULT_ALLOWED_PREFIXES: tuple[tuple[str, ...], ...] = (
        ("git", "status"),
        ("git", "diff"),
        ("git", "log"),
        ("python", "-m", "pytest"),
        ("pytest",),
        ("ruff", "check"),
        ("mypy",),
    )

    def __init__(
        self,
        workspace: Path | str,
        safety_policy: SafetyPolicy | None = None,
        timeout_seconds: float = 30.0,
        allowed_prefixes: Sequence[Sequence[str]] | None = None,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        root = Path(workspace).resolve()
        if not root.exists():
            raise FileNotFoundError(f"Workspace does not exist: {root}")
        if not root.is_dir():
            raise NotADirectoryError(f"Workspace is not a directory: {root}")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        self.workspace = root
        self.safety_policy = safety_policy or SafetyPolicy(dry_run=False)
        self.timeout_seconds = timeout_seconds
        prefixes = allowed_prefixes or self.DEFAULT_ALLOWED_PREFIXES
        self.allowed_prefixes = tuple(tuple(item) for item in prefixes)
        self.audit_logger = audit_logger or AuditLogger(root / ".ultron" / "audit.jsonl")

    def execute(
        self,
        action: str,
        approval: ApprovalRequest | None = None,
        correlation_id: str | None = None,
    ) -> ExecutionResult:
        """Evaluate and, when permitted, execute one allowlisted action."""
        run_correlation_id = correlation_id or str(uuid4())

        try:
            command = self._parse(action)
            self._validate_allowlist(command)
        except ExecutionDeniedError as exc:
            self.audit_logger.record_blocked(action, str(exc), run_correlation_id)
            raise

        approved = approval is not None and approval.status == ApprovalStatus.APPROVED
        decision = self.safety_policy.evaluate(action, approved=approved)

        if decision.risk == ActionRisk.BLOCKED:
            self.audit_logger.record(
                decision,
                status="denied",
                correlation_id=run_correlation_id,
            )
            raise ExecutionDeniedError(decision.reason)

        if decision.risk == ActionRisk.REQUIRES_APPROVAL and not approved:
            self.audit_logger.record(
                decision,
                status="denied",
                correlation_id=run_correlation_id,
            )
            raise ExecutionDeniedError("Explicit approval is required before execution.")

        if not decision.allowed:
            self.audit_logger.record(
                decision,
                status="denied",
                correlation_id=run_correlation_id,
            )
            raise ExecutionDeniedError(decision.reason)

        self.audit_logger.record(
            decision,
            status="approved",
            correlation_id=run_correlation_id,
        )

        try:
            completed = subprocess.run(
                list(command),
                cwd=self.workspace,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = self._decode_output(exc.stdout)
            stderr = self._decode_output(exc.stderr)
            self.audit_logger.record(
                decision,
                status="timed_out",
                correlation_id=run_correlation_id,
                return_code=-1,
                timed_out=True,
                error="Command execution exceeded the configured timeout.",
            )
            return ExecutionResult(
                action=action,
                command=command,
                return_code=-1,
                stdout=stdout,
                stderr=stderr,
                timed_out=True,
                correlation_id=run_correlation_id,
            )

        error = "" if completed.returncode == 0 else f"Command exited with code {completed.returncode}."
        self.audit_logger.record(
            decision,
            status="completed" if completed.returncode == 0 else "failed",
            correlation_id=run_correlation_id,
            return_code=completed.returncode,
            error=error,
        )

        return ExecutionResult(
            action=action,
            command=command,
            return_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            timed_out=False,
            correlation_id=run_correlation_id,
        )

    @staticmethod
    def _parse(action: str) -> tuple[str, ...]:
        command = tuple(shlex.split(action, posix=True))
        if not command:
            raise ExecutionDeniedError("Empty actions are not executable.")
        return command

    def _validate_allowlist(self, command: tuple[str, ...]) -> None:
        if not any(command[: len(prefix)] == prefix for prefix in self.allowed_prefixes):
            raise ExecutionDeniedError(
                "Command is outside the execution allowlist: " + " ".join(command)
            )

    @staticmethod
    def _decode_output(value: bytes | str | None) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return value
