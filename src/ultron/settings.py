"""Runtime configuration for ULTRON CODE."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class UltronSettings(BaseSettings):
    """Validated environment-backed ULTRON configuration."""

    model_config = SettingsConfigDict(
        env_prefix="ULTRON_",
        env_file=".env",
        extra="ignore",
    )

    workspace: Path = Path(".")
    state_path: Path = Path(".ultron/project.json")
    audit_path: Path = Path(".ultron/audit.jsonl")
    approvals_path: Path = Path(".ultron/approvals.json")
    runs_path: Path = Path(".ultron/runs.jsonl")
    dry_run: bool = True
    automation_enabled: bool = False
    poll_interval_seconds: float = Field(default=10.0, gt=0)
    max_iterations: int = Field(default=0, ge=0)
    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8765, ge=1, le=65535)

    def validate_paths(self) -> None:
        """Ensure mutable state locations are inside the configured workspace."""
        root = self.workspace.resolve()
        for candidate in (
            self.state_path,
            self.audit_path,
            self.approvals_path,
            self.runs_path,
        ):
            resolved = (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
            try:
                resolved.relative_to(root)
            except ValueError as exc:
                raise ValueError(f"ULTRON path escapes workspace: {resolved}") from exc
