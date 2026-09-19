from ultron.provider_registry import ProviderRegistry
from ultron.providers import MockProvider, ProviderKind


def test_registry_lists_default_providers() -> None:
    registry = ProviderRegistry()

    assert registry.available() == (
        ProviderKind.CHATGPT,
        ProviderKind.CLAUDE,
        ProviderKind.CURSOR,
        ProviderKind.MOCK,
    )


def test_registry_creates_mock_provider() -> None:
    registry = ProviderRegistry()

    provider = registry.create(
        "mock",
        summary="Working",
        progress=0.5,
        session_id="session-1",
    )

    assert isinstance(provider, MockProvider)
    assert provider.snapshot().summary == "Working"


def test_registry_creates_openai_adapter() -> None:
    registry = ProviderRegistry()

    provider = registry.create(
        "chatgpt",
        response_id="response-1",
        api_key="test-key",
    )

    assert provider.provider == ProviderKind.CHATGPT


def test_registry_rejects_unknown_provider() -> None:
    registry = ProviderRegistry()

    try:
        registry.create("unknown")
    except ValueError as exc:
        assert "unknown" in str(exc).lower()
    else:
        raise AssertionError("Unknown providers must be rejected.")
