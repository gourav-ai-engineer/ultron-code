from ultron.provider_runtime import (
    AnthropicModelsAdapter,
    CursorCloudRunAdapter,
    OpenAIResponseAdapter,
)
from ultron.providers import ProviderKind, ProviderStatus


def test_openai_response_adapter_reads_response() -> None:
    def fetcher(url, headers):
        assert url.endswith("/responses/resp-1")
        assert headers["Authorization"] == "Bearer test-key"
        return {"id": "resp-1", "status": "completed", "output_text": "Done"}

    adapter = OpenAIResponseAdapter("resp-1", api_key="test-key", fetcher=fetcher)

    assert adapter.provider == ProviderKind.CHATGPT
    assert adapter.health_check().status == ProviderStatus.AVAILABLE
    snapshot = adapter.snapshot()
    assert snapshot.session_id == "resp-1"
    assert snapshot.summary == "Done"
    assert snapshot.progress == 1.0


def test_anthropic_adapter_reports_api_availability() -> None:
    def fetcher(url, headers):
        assert url.endswith("/v1/models")
        assert headers["x-api-key"] == "test-key"
        return {"data": [{"id": "claude-test"}, {"id": "claude-test-2"}]}

    adapter = AnthropicModelsAdapter(api_key="test-key", fetcher=fetcher)

    assert adapter.health_check().status == ProviderStatus.AVAILABLE
    snapshot = adapter.snapshot()
    assert snapshot.provider == ProviderKind.CLAUDE
    assert snapshot.session_id is None
    assert snapshot.summary.endswith("2 models visible.")
    assert snapshot.progress is None


def test_cursor_cloud_run_adapter_reads_run() -> None:
    def fetcher(url, headers):
        assert url.endswith("/agents/agent-1/runs/run-1")
        assert headers["Authorization"] == "Bearer cursor-key"
        return {"id": "run-1", "status": "RUNNING", "result": "Building the feature"}

    adapter = CursorCloudRunAdapter(
        "agent-1",
        "run-1",
        api_key="cursor-key",
        fetcher=fetcher,
    )

    snapshot = adapter.snapshot()
    assert snapshot.provider == ProviderKind.CURSOR
    assert snapshot.session_id == "run-1"
    assert snapshot.summary == "Building the feature"
    assert snapshot.progress == 0.5
