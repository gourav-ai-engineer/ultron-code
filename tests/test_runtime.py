from pathlib import Path

from ultron.providers import MockProvider
from ultron.runtime import UltronRuntime
from ultron.settings import UltronSettings


def test_runtime_persists_observations(tmp_path: Path) -> None:
    settings = UltronSettings(
        workspace=tmp_path,
        runs_path=Path(".ultron") / "runs.jsonl",
    )
    runtime = UltronRuntime(settings)

    run = runtime.observe(
        MockProvider(summary="Working", progress=0.5),
    )

    assert run.run_id
    assert runtime.run_count == 1
