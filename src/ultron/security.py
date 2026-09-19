"""Secret redaction and workspace security helpers."""

import re
from pathlib import Path

_SECRET_PATTERNS = (
    re.compile(r"(sk-[A-Za-z0-9_-]{12,})"),
    re.compile(r"(gh[pousr]_[A-Za-z0-9_]{20,})"),
    re.compile(r"(Bearer\s+)[A-Za-z0-9._-]{12,}", re.IGNORECASE),
)


def redact_secrets(text: str) -> str:
    """Redact common API-token representations from logs and messages."""
    result = text
    result = _SECRET_PATTERNS[0].sub("[REDACTED]", result)
    result = _SECRET_PATTERNS[1].sub("[REDACTED]", result)
    result = _SECRET_PATTERNS[2].sub(r"\1[REDACTED]", result)
    return result


def ensure_within_workspace(root: Path | str, target: Path | str) -> Path:
    """Resolve a target and reject paths outside the configured workspace."""
    workspace = Path(root).resolve()
    candidate = Path(target).resolve()
    try:
        candidate.relative_to(workspace)
    except ValueError as exc:
        raise ValueError(f"Path escapes workspace: {candidate}") from exc
    return candidate
