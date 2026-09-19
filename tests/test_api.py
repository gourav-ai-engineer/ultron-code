from pathlib import Path

import pytest

from ultron.runtime import UltronRuntime
from ultron.settings import UltronSettings


def make_client(tmp_path: Path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from ultron.api import create_app

    runtime = UltronRuntime(
        UltronSettings(
            workspace=tmp_path,
            runs_path=Path(".ultron/runs.jsonl"),
        )
    )
    return TestClient(create_app(runtime))


def test_health_endpoint(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["dry_run"] is True


def test_providers_endpoint(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.get("/providers")

    assert response.status_code == 200
    assert "mock" in response.json()["providers"]
