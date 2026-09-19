"""Controlled local action execution for ULTRON CODE."""

from dataclasses import dataclass
from pathlib import Path
import shlex
import subprocess
from typing import Sequence

from .approval import ApprovalRequest, ApprovalStatus
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

    def execute(
        self,
        action: str,
        approval: ApprovalRequest | None = None,
    ) -> ExecutionResult:
        """Evaluate and, when permitted, execute one allowlisted action."""
        command = self._parse(action)
        self._validate_allowlist(command)

        approved = approval is not None and approval.status == ApprovalStatus.APPROVED
        decision = self.safety_policy.evaluate(action, approved=approved)

        if decision.risk == ActionRisk.BLOCKED:
            raise ExecutionDeniedError(decision.reason)
        if decision.risk == ActionRisk.REQUIRES_APPROVAL and not approved:
            raise ExecutionDeniedError("Explicit approval is required before execution.")
        if not decision.allowed:
            raise ExecutionDeniedError(decision.reason)

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
            return ExecutionResult(
                action=action,
                command=command,
                return_code=-1,
                stdout=stdout,
                stderr=stderr,
                timed_out=True,
            )

        return ExecutionResult(
            action=action,
            command=command,
            return_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            timed_out=False,
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
