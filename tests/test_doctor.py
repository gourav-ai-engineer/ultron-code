from pathlib import Path

from ultron.doctor import Doctor
from ultron.settings import UltronSettings


def test_doctor_reports_required_environment(tmp_path: Path) -> None:
    doctor = Doctor(UltronSettings(workspace=tmp_path))

    names = {item.name for item in doctor.check()}

    assert {"python", "workspace", "git", "configuration_paths"} <= names
