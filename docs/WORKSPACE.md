# Workspace Monitoring

`WorkspaceObserver` provides read-only local workspace snapshots.

It reports the resolved root, current Git branch, modified files, untracked files, and whether Git metadata was detected.

## Safety boundaries

- Does not write, delete, stage, commit, or execute project commands.
- Uses bounded Git subprocess calls with a short timeout.
- Treats missing Git metadata or unavailable Git as an observable state.

This component is a foundation for future progress detection and provider feedback correlation.
