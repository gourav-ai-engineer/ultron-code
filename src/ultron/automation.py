"""Optional screen and keyboard automation guarded by ULTRON safety controls."""

from dataclasses import dataclass
from pathlib import Path

from .approval import ApprovalRequest, ApprovalStatus
from .safety import ActionRisk, SafetyPolicy


class AutomationUnavailableError(RuntimeError):
    """Raised when optional UI automation dependencies are unavailable."""


class AutomationDeniedError(RuntimeError):
    """Raised when automation is not explicitly authorized."""


@dataclass(frozen=True)
class ScreenSnapshot:
    """Minimal metadata for a captured screen image."""

    path: str
    width: int
    height: int


class ScreenObserver:
    """Capture a screenshot without interacting with the UI."""

    def capture(self, path: Path | str) -> ScreenSnapshot:
        try:
            import pyautogui
        except ImportError as exc:
            raise AutomationUnavailableError(
                "Install the optional automation dependencies to capture screens."
            ) from exc

        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        image = pyautogui.screenshot()
        image.save(target)
        return ScreenSnapshot(str(target), image.width, image.height)


class KeyboardController:
    """Type or press keys through an approved or explicitly trusted operation."""

    def __init__(
        self,
        safety_policy: SafetyPolicy | None = None,
        trusted_mode: bool = False,
    ) -> None:
        self.safety_policy = safety_policy or SafetyPolicy(dry_run=True)
        self.trusted_mode = trusted_mode

    def write(
        self,
        text: str,
        approval: ApprovalRequest | None = None,
    ) -> None:
        self._authorize("type text", approval)
        self._pyautogui().write(text)

    def press(
        self,
        key: str,
        approval: ApprovalRequest | None = None,
    ) -> None:
        self._authorize(f"press {key}", approval)
        self._pyautogui().press(key)

    def hotkey(
        self,
        *keys: str,
        approval: ApprovalRequest | None = None,
    ) -> None:
        self._authorize("hotkey " + " ".join(keys), approval)
        self._pyautogui().hotkey(*keys)

    def _authorize(self, action: str, approval: ApprovalRequest | None) -> None:
        if self.safety_policy.dry_run:
            raise AutomationDeniedError("Keyboard automation is disabled in dry-run mode.")

        approved = approval is not None and approval.status == ApprovalStatus.APPROVED
        if not approved and not self.trusted_mode:
            raise AutomationDeniedError(
                "Keyboard automation requires explicit approval or trusted mode."
            )

        decision = self.safety_policy.evaluate(
            action,
            approved=approved or self.trusted_mode,
        )
        if decision.risk == ActionRisk.BLOCKED or not decision.allowed:
            raise AutomationDeniedError(decision.reason)

    @staticmethod
    def _pyautogui():
        try:
            import pyautogui
        except ImportError as exc:
            raise AutomationUnavailableError(
                "Install the optional automation dependencies for keyboard control."
            ) from exc
        return pyautogui
