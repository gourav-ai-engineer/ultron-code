from dataclasses import dataclass

from ultron.approval import ApprovalRequest, ApprovalStatus
from ultron.desktop import DesktopInteractionConfig, DesktopProviderAdapter
from ultron.interaction import InteractionResult
from ultron.safety import ActionRisk


@dataclass
class FakeWindowController:
    focused: list[str]

    def find_and_focus(self, title_contains: str) -> str:
        self.focused.append(title_contains)
        return "ChatGPT - Browser"


class FakeKeyboard:
    def __init__(self) -> None:
        self.operations: list[tuple[str, str]] = []

    def write(self, text: str, approval=None) -> None:
        self.operations.append(("write", text))

    def press(self, key: str, approval=None) -> None:
        self.operations.append(("press", key))


def approved() -> ApprovalRequest:
    return ApprovalRequest(
        request_id="req-1",
        action="send prompt",
        rationale="Continue coding",
        risk=ActionRisk.REQUIRES_APPROVAL,
        status=ApprovalStatus.APPROVED,
        requested_at="2026-09-19T00:00:00+00:00",
        resolved_at="2026-09-19T00:01:00+00:00",
        resolution_note="Approved",
        correlation_id="run-1",
    )


def test_desktop_adapter_requires_enablement() -> None:
    keyboard = FakeKeyboard()
    adapter = DesktopProviderAdapter(
        "chatgpt",
        DesktopInteractionConfig(window_title="ChatGPT", enabled=False),
        keyboard=keyboard,
        windows=FakeWindowController([]),
    )

    try:
        adapter.send_prompt("continue", "run-1", approval=approved())
    except Exception as exc:
        assert "disabled" in str(exc).lower()
    else:
        raise AssertionError("Disabled automation must not send.")


def test_desktop_adapter_delivers_after_approval() -> None:
    keyboard = FakeKeyboard()
    windows = FakeWindowController([])
    adapter = DesktopProviderAdapter(
        "chatgpt",
        DesktopInteractionConfig(window_title="ChatGPT", enabled=True),
        keyboard=keyboard,
        windows=windows,
    )

    result = adapter.send_prompt("continue", "run-1", approval=approved())

    assert isinstance(result, InteractionResult)
    assert result.accepted is True
    assert windows.focused == ["ChatGPT"]
    assert keyboard.operations == [("write", "continue"), ("press", "enter")]
