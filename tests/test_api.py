import pytest

from ultron.runtime import UltronRuntime
from ultron.settings import UltronSettings


def test_health_endpoint() -> None:
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    runtime = UltronRuntime(UltronSettings())
    from ultron.api import create_app

    client = TestClient(create_app(runtime))
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["dry_run"] is True
