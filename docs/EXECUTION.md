# Controlled Action Execution

Phase 11 introduced the first execution boundary for ULTRON CODE. Phase 12 connects that boundary to the persistent audit trail.

## Execution rules

The executor:

- runs commands with `shell=False`
- executes only from an explicit command allowlist
- confines execution to one configured workspace
- applies a configurable timeout
- captures stdout and stderr for the caller
- honors the safety policy and emergency stop
- requires an approved `ApprovalRequest` when the safety policy requires approval
- returns a structured result containing a correlation ID
- writes execution lifecycle events to the audit logger

## Current command allowlist

The default allowlist contains narrowly scoped developer workflows:

- `git status ...`
- `git diff ...`
- `git log ...`
- `python -m pytest ...`
- `pytest ...`
- `ruff check ...`
- `mypy ...`

The executor intentionally does not provide a generic shell. Write-heavy operations such as arbitrary scripts, package installation, deployment, filesystem deletion, or shell pipelines must be added through a separately reviewed capability.

## Safety and audit sequence

`action -> parse -> allowlist -> safety policy -> approval check -> audit -> subprocess -> outcome audit`

An allowlist rejection is audited as a denied attempt. A safety rejection is audited before no subprocess is started. Successful execution records a separate outcome event using the same correlation ID.

Captured command output is returned to the caller but is not automatically copied into the persistent audit trail.

## Next integration

Future phases can connect the correlation ID to provider sessions, workspace snapshots, approval requests, and phase transitions to build a complete end-to-end execution timeline.
