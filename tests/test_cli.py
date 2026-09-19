from typer.testing import CliRunner

from ultron.cli import app


runner = CliRunner()


def test_status_command() -> None:
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "ULTRON CODE" in result.stdout
    assert "dry-run" in result.stdout
