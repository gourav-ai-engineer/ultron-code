from pathlib import Path

import pytest

from ultron.settings import UltronSettings


def test_settings_defaults_to_safe_mode(tmp_path: Path) -> None:
    settings = UltronSettings(workspace=tmp_path)

    assert settings.dry_run is True
    assert settings.automation_enabled is False


def test_settings_rejects_paths_outside_workspace(tmp_path: Path) -> None:
    settings = UltronSettings(workspace=tmp_path, state_path=Path("..") / "project.json")

    with pytest.raises(ValueError, match="escapes workspace"):
        settings.validate_paths()
