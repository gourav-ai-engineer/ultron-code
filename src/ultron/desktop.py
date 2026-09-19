"""Controlled desktop provider interaction for UI-only fallback workflows."""

from dataclasses import dataclass
import platform
import time

from .approval import ApprovalRequest, ApprovalStatus
from .automation import AutomationDeniedError, KeyboardController
from .interaction import InteractionResult
from .safety import SafetyPolicy
from .security import redact_secrets


class WindowNotFoundError(RuntimeError):
    """Raised when the requested desktop window cannot be focused."""


class WindowController:
    """Find and focus a desktop window by configurable title substring."""

    def find_and_focus(self, title_contains: str) -> str:
        if not title_contains.strip():
            raise ValueError("title_contains must not be empty")

        if platform.system() != "Windows":
            raise WindowNotFoundError("Desktop window focusing currently requires Windows.")

        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        matches: list[tuple[int, str]] = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        def callback(hwnd, _lparam):
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value
            if title_contains.lower() in title.lower():
                matches.append((hwnd, title))
            return True

        user32.EnumWindows(callback, 0)
        if not matches:
            raise WindowNotFoundError(f"No window contains title: {title_contains}")

        hwnd, title = matches[0]
        user32.SetForegroundWindow(hwnd)
        return title


@dataclass(frozen=True)
class DesktopInteractionConfig:
    window_title: str
    submit_key: str = "enter"
    focus_delay_seconds: float = 0.5
    enabled: bool = False
    trusted_automation: bool = False


class DesktopProviderAdapter:
    """Deliver a prompt through a focused desktop application window."""

    def __init__(
        self,
        provider: str,
        config: DesktopInteractionConfig,
        keyboard: KeyboardController | None = None,
        windows: WindowController | None = None,
    ) -> None:
        self._provider = provider
        self.config = config
        self.keyboard = keyboard or KeyboardController(
            SafetyPolicy(dry_run=not config.enabled),
            trusted_mode=config.trusted_automation,
        )
        self.windows = windows or WindowController()

    @property
    def provider(self) -> str:
        return self._provider

    def send_prompt(
        self,
        prompt: str,
        correlation_id: str,
        approval: ApprovalRequest | None = None,
        requires_approval: bool = True,
    ) -> InteractionResult:
        """Focus the configured window, type the prompt, and submit it."""
        if not self.config.enabled:
            raise AutomationDeniedError("Desktop automation is disabled.")

        if requires_approval and (
            approval is None or approval.status != ApprovalStatus.APPROVED
        ):
            return InteractionResult(
                interaction_id=f"desktop-{correlation_id}",
                provider=self.provider,
                accepted=False,
                message="Desktop interaction requires explicit approval.",
                correlation_id=correlation_id,
            )

        if not requires_approval and not self.config.trusted_automation and approval is None:
            return InteractionResult(
                interaction_id=f"desktop-{correlation_id}",
                provider=self.provider,
                accepted=False,
                message="Trusted automation mode is disabled.",
                correlation_id=correlation_id,
            )

        title = self.windows.find_and_focus(self.config.window_title)
        time.sleep(self.config.focus_delay_seconds)
        safe_prompt = redact_secrets(prompt)
        self.keyboard.write(safe_prompt, approval=approval)
        self.keyboard.press(self.config.submit_key, approval=approval)
        return InteractionResult(
            interaction_id=f"desktop-{correlation_id}",
            provider=self.provider,
            accepted=True,
            message=f"Prompt delivered to window: {title}",
            correlation_id=correlation_id,
        )
