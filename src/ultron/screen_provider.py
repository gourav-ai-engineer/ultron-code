"""Screen-based provider observer for UI-only integrations."""

from dataclasses import dataclass
from pathlib import Path

from .automation import AutomationUnavailableError, ScreenObserver
from .desktop import WindowController, WindowNotFoundError
from .providers import ProviderHealth, ProviderKind, ProviderSnapshot, ProviderStatus
from .screen_reader import PytesseractScreenReader, ScreenText, ScreenTextUnavailableError


@dataclass
class ScreenProviderAdapter:
    """Read provider state from a focused desktop window screenshot."""

    provider_kind: ProviderKind
    window_title: str
    screenshot_path: Path = Path(".ultron/screens/provider.png")
    observer: ScreenObserver | None = None
    windows: WindowController | None = None
    reader: PytesseractScreenReader | None = None

    @property
    def provider(self) -> ProviderKind:
        return self.provider_kind

    def health_check(self) -> ProviderHealth:
        try:
            self._capture()
        except (AutomationUnavailableError, WindowNotFoundError, ScreenTextUnavailableError) as exc:
            return ProviderHealth(
                self.provider,
                ProviderStatus.UNAVAILABLE,
                str(exc),
            )
        return ProviderHealth(
            self.provider,
            ProviderStatus.AVAILABLE,
            f"Desktop window '{self.window_title}' is observable.",
        )

    def snapshot(self) -> ProviderSnapshot:
        title, text = self._capture()
        return ProviderSnapshot(
            provider=self.provider,
            session_id=title,
            summary=text.text or "No visible provider text detected.",
            progress=self._progress(text.text),
        )

    def _capture(self) -> tuple[str, ScreenText]:
        windows = self.windows or WindowController()
        observer = self.observer or ScreenObserver()
        reader = self.reader or PytesseractScreenReader()

        title = windows.find_and_focus(self.window_title)
        observer.capture(self.screenshot_path)
        text = reader.read(self.screenshot_path)
        return title, text

    @staticmethod
    def _progress(text: str) -> float | None:
        normalized = text.lower()
        if any(token in normalized for token in ("completed", "task complete", "done")):
            return 1.0
        if any(token in normalized for token in ("error", "failed", "blocked")):
            return 0.0
        if text.strip():
            return 0.5
        return None
