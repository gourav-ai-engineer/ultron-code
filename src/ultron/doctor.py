"""Environment and configuration diagnostics for ULTRON CODE."""

from dataclasses import dataclass
import importlib.util
import shutil
import sys
from pathlib import Path

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

        diagnostics.append(
            Diagnostic(
                "python",
                sys.version_info >= (3, 11) and sys.version_info < (3, 15),
                f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            )
        )
        diagnostics.append(
            Diagnostic(
                "workspace",
                self.settings.workspace.exists() and self.settings.workspace.is_dir(),
                str(self.settings.workspace.resolve()),
            )
        )
        diagnostics.append(
            Diagnostic(
                "git",
                shutil.which("git") is not None,
                "git available on PATH" if shutil.which("git") else "git not found on PATH",
            )
        )
        diagnostics.append(
            Diagnostic(
                "configuration_paths",
                self._check_paths(),
                "configured paths remain inside the workspace"
                if self._check_paths()
                else "one or more configured paths escape the workspace",
            )
        )
        diagnostics.append(self._module("fastapi", "API dependency"))
        diagnostics.append(self._module("pyautogui", "desktop automation dependency"))
        diagnostics.append(self._module("PIL", "OCR image dependency"))
        diagnostics.append(self._module("pytesseract", "OCR Python dependency"))
        diagnostics.append(
            Diagnostic(
                "tesseract",
                shutil.which("tesseract") is not None
                or bool(self._tesseract_override()),
                "Tesseract executable available"
                if shutil.which("tesseract") or self._tesseract_override()
                else "Tesseract executable not found",
            )
        )
        diagnostics.append(
            Diagnostic(
                "openai_key",
                bool(self._env("OPENAI_API_KEY")),
                "configured" if self._env("OPENAI_API_KEY") else "not configured",
            )
        )
        diagnostics.append(
            Diagnostic(
                "anthropic_key",
                bool(self._env("ANTHROPIC_API_KEY")),
                "configured" if self._env("ANTHROPIC_API_KEY") else "not configured",
            )
        )
        diagnostics.append(
            Diagnostic(
                "cursor_key",
                bool(self._env("CURSOR_API_KEY")),
                "configured" if self._env("CURSOR_API_KEY") else "not configured",
            )
        )

        return tuple(diagnostics)

    def healthy(self, include_optional: bool = False) -> bool:
        """Return whether required diagnostics pass."""
        diagnostics = self.check()
        required_prefixes = {"python", "workspace", "git", "configuration_paths"}
        for item in diagnostics:
            if item.name in required_prefixes and not item.ok:
                return False
            if include_optional and item.name in {
                "fastapi",
                "pyautogui",
                "PIL",
                "pytesseract",
                "tesseract",
            } and not item.ok:
                return False
        return True

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
        import os

        return os.getenv(name, "").strip()

    def _tesseract_override(self) -> str:
        override = self._env("ULTRON_TESSERACT_CMD")
        if not override:
            return ""
        return override if Path(override).exists() else ""
