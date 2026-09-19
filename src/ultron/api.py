"""Optional local HTTP API for ULTRON CODE."""

from typing import Any
import hmac

from .provider_runtime import ProviderRequestError
from .runtime import UltronRuntime


def create_app(runtime: UltronRuntime | None = None):
    """Create the FastAPI application without importing FastAPI at module load."""
    try:
        from fastapi import FastAPI, Header, HTTPException
        from fastapi.staticfiles import StaticFiles
        from pydantic import BaseModel, Field
    except ImportError as exc:
        raise RuntimeError(
            "Install the 'api' optional dependency to use the ULTRON HTTP API."
        ) from exc

    runtime = runtime or UltronRuntime()
    app = FastAPI(title="ULTRON CODE", version="0.9.0")

    class ObservationRequest(BaseModel):
        provider: str = "mock"
        response_id: str | None = None
        agent_id: str | None = None
        provider_run_id: str | None = None
        summary: str = "No activity recorded."
        progress: float | None = Field(default=None, ge=0.0, le=1.0)
        session_id: str | None = None

    def require_token(authorization: str | None) -> None:
        configured = runtime.settings.api_token
        if configured is None:
            return
        expected = f"Bearer {configured.get_secret_value()}"
        if authorization is None or not hmac.compare_digest(authorization, expected):
            raise HTTPException(status_code=401, detail="Unauthorized.")

    dashboard_root = runtime.settings.resolve_path(runtime.settings.dashboard_path)
    if dashboard_root.exists() and dashboard_root.is_dir():
        app.mount(
            "/dashboard",
            StaticFiles(directory=dashboard_root, html=True),
            name="dashboard",
        )

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "version": app.version,
            "workspace": str(runtime.settings.workspace.resolve()),
            "dry_run": runtime.settings.dry_run,
            "automation_enabled": runtime.settings.automation_enabled,
        }

    @app.get("/providers")
    def providers(authorization: str | None = Header(default=None)) -> dict[str, list[str]]:
        require_token(authorization)
        return {"providers": [item.value for item in runtime.registry.available()]}

    @app.get("/runs")
    def runs(authorization: str | None = Header(default=None)) -> list[dict[str, object]]:
        require_token(authorization)
        return runtime.run_store.all()

    @app.get("/runs/latest")
    def latest_run(authorization: str | None = Header(default=None)) -> dict[str, object]:
        require_token(authorization)
        latest = runtime.run_store.latest()
        if latest is None:
            raise HTTPException(status_code=404, detail="No workflow runs recorded.")
        return latest

    @app.post("/runs/observe")
    def observe(
        request: ObservationRequest,
        authorization: str | None = Header(default=None),
    ) -> dict[str, object]:
        require_token(authorization)

        kwargs: dict[str, object]
        if request.provider == "mock":
            kwargs = {
                "summary": request.summary,
                "progress": request.progress,
                "session_id": request.session_id,
            }
        elif request.provider == "chatgpt":
            if request.response_id is None:
                raise HTTPException(status_code=400, detail="response_id is required.")
            kwargs = {"response_id": request.response_id}
        elif request.provider == "cursor":
            if request.agent_id is None or request.provider_run_id is None:
                raise HTTPException(
                    status_code=400,
                    detail="agent_id and provider_run_id are required.",
                )
            kwargs = {
                "agent_id": request.agent_id,
                "run_id": request.provider_run_id,
            }
        elif request.provider == "claude":
            kwargs = {}
        else:
            raise HTTPException(status_code=400, detail="Unknown provider.")

        try:
            provider = runtime.provider(request.provider, **kwargs)
            run = runtime.observe(provider, runtime.project())
        except ProviderRequestError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        return {
            "run_id": run.run_id,
            "provider": run.provider.provider.value,
            "state": run.assessment.state.value,
            "decision": run.decision.kind.value,
            "rationale": run.decision.rationale,
            "prompt": run.prompt.prompt,
        }

    return app
