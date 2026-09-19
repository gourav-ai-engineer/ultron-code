from pathlib import Path

import pytest

from ultron.security import ensure_within_workspace, redact_secrets


def test_redacts_common_secrets() -> None:
    text = "token=sk-abcdefghijklmnop1234 Bearer abcdefghijklmnop"
    redacted = redact_secrets(text)

    assert "sk-abcdefghijkl" not in redacted
    assert "Bearer [REDACTED]" in redacted


def test_rejects_path_escape(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="escapes workspace"):
        ensure_within_workspace(tmp_path, tmp_path / ".." / "outside.txt")
