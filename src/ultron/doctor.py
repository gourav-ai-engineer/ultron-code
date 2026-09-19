"""Environment and configuration diagnostics for ULTRON CODE."""

from dataclasses import dataclass
import importlib.util
import os
from pathlib import Path
import shutil
import sys

from .settings import UltronSettings


@dataclass(frozen=True)
class Diagnostic:
    """One environment diagnostic result."""

    name: str
    ok: bool
    detail: str


class Doctor:
    """Run non-mutating diagnostics for the local ULTRON runtime."""

    def __init__(self, settings: UltronSettings | None = None) -> None:
        self.settings = settings or UltronSettings()

    def check(self) -> tuple[Diagnostic, ...]:
        diagnostics: list[Diagnostic] = []

        python_ok = sys.version_info >= (3, 11) and sys.version_info < (3, 15)
        diagnostics.append(
            Diagnostic(
                "python",
                python_ok,
                (
                    f"Python {sys.version_info.major}."
                    f"{sys.version_info.minor}."
                    f"{sys.version_info.micro}"
                ),
            )
        )

        workspace_ok = self.settings.workspace.exists() and self.settings.workspace.is_dir()
        diagnostics.append(
            Diagnostic(
                "workspace",
                workspace_ok,
                str(self.settings.workspace.resolve()),
            )
        )

        git_path = shutil.which("git")
        diagnostics.append(
            Diagnostic(
                "git",
                git_path is not None,
                "git available on PATH" if git_path else "git not found on PATH",
            )
        )

        paths_ok = self._check_paths()
        diagnostics.append(
            Diagnostic(
                "configuration_paths",
                paths_ok,
                (
                    "configured paths remain inside the workspace"
                    if paths_ok
                    else "one or more configured paths escape the workspace"
                ),
            )
        )

        diagnostics.append(self._module("fastapi", "API dependency"))
        diagnostics.append(self._module("pyautogui", "desktop automation dependency"))
        diagnostics.append(self._module("PIL", "OCR image dependency"))
        diagnostics.append(self._module("pytesseract", "OCR Python dependency"))

        tesseract_path = shutil.which("tesseract") or self._tesseract_override()
        diagnostics.append(
            Diagnostic(
                "tesseract",
                tesseract_path is not None,
                (
                    "Tesseract executable available"
                    if tesseract_path
                    else "Tesseract executable not found"
                ),
            )
        )

        diagnostics.append(
            Diagnostic(
                "gemini_api_key",
                self.settings.gemini_api_key is not None,
                "configured" if self.settings.gemini_api_key else "not configured",
            )
        )
        diagnostics.append(
            Diagnostic(
                "openrouter_api_key",
                self.settings.openrouter_api_key is not None,
                "configured" if self.settings.openrouter_api_key else "not configured",
            )
        )

        ollama_path = shutil.which("ollama")
        diagnostics.append(
            Diagnostic(
                "ollama",
                ollama_path is not None,
                "Ollama executable available" if ollama_path else "Ollama not installed",
            )
        )

        return tuple(diagnostics)

    def healthy(self, include_optional: bool = False) -> bool:
        """Return whether required diagnostics pass."""
        diagnostics = self.check()
        required = {"python", "workspace", "git", "configuration_paths"}
        optional = {
            "fastapi",
            "pyautogui",
            "PIL",
            "pytesseract",
            "tesseract",
            "gemini_api_key",
            "openrouter_api_key",
            "ollama",
        }

        return all(
            item.ok
            for item in diagnostics
            if item.name in required or (include_optional and item.name in optional)
        )

    def _check_paths(self) -> bool:
        try:
            self.settings.validate_paths()
        except ValueError:
            return False
        return True

    @staticmethod
    def _module(name: str, label: str) -> Diagnostic:
        present = importlib.util.find_spec(name) is not None
        return Diagnostic(
            name,
            present,
            f"{label} available" if present else f"{label} not installed",
        )

    @staticmethod
    def _env(name: str) -> str:
        return os.getenv(name, "").strip()

    def _tesseract_override(self) -> str | None:
        override = self._env("ULTRON_TESSERACT_CMD")
        if not override:
            return None
        path = Path(override)
        return str(path) if path.exists() and path.is_file() else None
