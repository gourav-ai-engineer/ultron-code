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



def test_settings_load_free_provider_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test")
    monkeypatch.setenv("OPENROUTER_API_KEY", "router-test")
    monkeypatch.setenv("OLLAMA_MODEL", "local-test")

    settings = UltronSettings()

    assert settings.gemini_api_key is not None
    assert settings.gemini_api_key.get_secret_value() == "gemini-test"
    assert settings.openrouter_api_key is not None
    assert settings.openrouter_api_key.get_secret_value() == "router-test"
    assert settings.ollama_model == "local-test"
