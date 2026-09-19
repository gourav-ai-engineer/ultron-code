from pathlib import Path

from ultron.workspace import WorkspaceObserver


def test_snapshot_for_non_git_directory(tmp_path: Path) -> None:
    snapshot = WorkspaceObserver(tmp_path).snapshot()
    assert snapshot.root == str(tmp_path.resolve())
    assert snapshot.changed_files == ()
    assert snapshot.untracked_files == ()
    assert snapshot.git_available is False
