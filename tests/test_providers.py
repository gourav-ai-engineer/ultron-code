from ultron.providers import MockProvider, ProviderKind, ProviderStatus


def test_mock_provider_health() -> None:
    health = MockProvider().health_check()
    assert health.provider == ProviderKind.MOCK
    assert health.status == ProviderStatus.AVAILABLE


def test_mock_provider_snapshot() -> None:
    snapshot = MockProvider(summary="Working", progress=0.5, session_id="session-1").snapshot()
    assert snapshot.summary == "Working"
    assert snapshot.progress == 0.5
    assert snapshot.session_id == "session-1"
