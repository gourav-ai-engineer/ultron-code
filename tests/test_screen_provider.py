from dataclasses import dataclass
from pathlib import Path

from ultron.providers import ProviderKind, ProviderStatus
from ultron.screen_provider import ScreenProviderAdapter
from ultron.screen_reader import ScreenText


@dataclass
class FakeWindows:
    def find_and_focus(self, title: str) -> str:
        return title + " - Browser"


@dataclass
class FakeObserver:
    def capture(self, path: Path | str):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fake", encoding="utf-8")
        return type("Snapshot", (), {"path": str(path), "width": 1, "height": 1})()


@dataclass
class FakeReader:
    def read(self, path: Path | str) -> ScreenText:
        return ScreenText(str(path), "Implementation complete")


def test_screen_provider_reads_window_text(tmp_path) -> None:
    adapter = ScreenProviderAdapter(
        ProviderKind.CHATGPT,
        "ChatGPT",
        screenshot_path=tmp_path / "screen.png",
        windows=FakeWindows(),
        observer=FakeObserver(),
        reader=FakeReader(),
    )

    assert adapter.health_check().status == ProviderStatus.AVAILABLE
    snapshot = adapter.snapshot()

    assert snapshot.provider == ProviderKind.CHATGPT
    assert snapshot.session_id == "ChatGPT - Browser"
    assert snapshot.progress == 1.0
    assert "complete" in snapshot.summary.lower()
