# ULTRON Operations

## Safe startup

The runtime starts in dry-run mode and UI automation disabled.

Typical local sequence:

`ultron init`

`ultron plan`

`ultron workflow-run --provider mock --provider-summary "Working" --progress 0.5`

## Loop control

The workflow loop can run for a bounded number of iterations. A stop request is cooperative; persistent emergency-stop state is stored under `.ultron/control.json`.

An emergency stop is treated as authoritative until an operator explicitly clears it.

## API

The API binds to `127.0.0.1` by default. It exposes observation and read-only runtime information. Configure an API token before exposing it outside the local machine.

## UI automation

UI automation is an explicit fallback. Enable it only when required, configure a target window title, and approve each prompt-delivery operation.

## Recovery

Run history is stored in `.ultron/runs.jsonl`. The recovery manager can identify the last run while respecting paused/emergency-stop state.

## Logs and secrets

Audit events intentionally avoid persisting command stdout/stderr. API keys are read from environment variables and are not stored in provider snapshots.
