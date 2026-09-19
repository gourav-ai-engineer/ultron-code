import pytest

from ultron.automation import AutomationDeniedError, KeyboardController
from ultron.safety import SafetyPolicy


def test_keyboard_is_denied_in_dry_run() -> None:
    controller = KeyboardController(SafetyPolicy(dry_run=True))

    with pytest.raises(AutomationDeniedError, match="dry-run"):
        controller.write("hello")
