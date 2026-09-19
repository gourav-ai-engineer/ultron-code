from ultron.provider_registry import ProviderRegistry
from ultron.workspace import WorkspaceObserver
from ultron.workflow import WorkflowEngine


def test_registered_openai_adapter_flows_through_workflow(tmp_path) -> None:
    def fetcher(url, headers):
        assert url.endswith("/responses/response-42")
        assert headers["Authorization"] == "Bearer test-key"
        return {
            "id": "response-42",
            "status": "in_progress",
            "output_text": "Implementing the requested change.",
        }

    registry = ProviderRegistry()
    provider = registry.create(
        "chatgpt",
        response_id="response-42",
        api_key="test-key",
        fetcher=fetcher,
    )

    run = WorkflowEngine(WorkspaceObserver(tmp_path)).observe(
        provider,
        has_active_phase=True,
    )

    assert run.provider.provider.value == "chatgpt"
    assert run.provider.session_id == "response-42"
    assert run.assessment.state.value == "progressing"
    assert run.decision.kind.value == "wait"
