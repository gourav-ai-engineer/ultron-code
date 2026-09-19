"""Provider adapter contracts for ULTRON CODE."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class ProviderKind(StrEnum):
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    CURSOR = "cursor"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    MOCK = "mock"


class ProviderStatus(StrEnum):
    UNKNOWN = "unknown"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class ProviderHealth:
    provider: ProviderKind
    status: ProviderStatus
    message: str


@dataclass(frozen=True)
class ProviderSnapshot:
    provider: ProviderKind
    session_id: str | None
    summary: str
    progress: float | None = None


class ProviderAdapter(Protocol):
    """Read-only contract implemented by each external provider adapter."""

    @property
    def provider(self) -> ProviderKind: ...

    def health_check(self) -> ProviderHealth: ...

    def snapshot(self) -> ProviderSnapshot: ...


@dataclass
class MockProvider:
    """Deterministic provider used for local development and tests."""

    summary: str = "No activity recorded."
    progress: float | None = 0.0
    session_id: str | None = None

    @property
    def provider(self) -> ProviderKind:
        return ProviderKind.MOCK

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider=self.provider,
            status=ProviderStatus.AVAILABLE,
            message="Mock provider is available locally.",
        )

    def snapshot(self) -> ProviderSnapshot:
        return ProviderSnapshot(
            provider=self.provider,
            session_id=self.session_id,
            summary=self.summary,
            progress=self.progress,
        )
