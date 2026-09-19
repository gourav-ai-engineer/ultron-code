# Controlled Action Execution

Phase 11 introduces the first execution boundary for ULTRON CODE.

## Execution rules

The executor:

- runs commands with `shell=False`
- executes only from an explicit command allowlist
- confines execution to one configured workspace
- applies a configurable timeout
- captures stdout and stderr
- honors the safety policy and emergency stop
- requires an approved `ApprovalRequest` when the safety policy requires approval
- returns structured results instead of mutating orchestrator state

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

## Safety model

The execution sequence is:

`action -> allowlist -> safety policy -> approval check -> subprocess -> structured result`

A blocked action never reaches the subprocess layer. Dry-run mode also prevents execution.

## Next integration

Future phases can attach execution results to the audit logger, correlate test output with workspace/provider state, and add additional reviewed command capabilities.
