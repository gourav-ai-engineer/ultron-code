# Audit Trail

ULTRON CODE records safety decisions and execution outcomes as JSON Lines in `.ultron/audit.jsonl`.

Each event contains:

- `event_id`: unique event identifier
- `action`: proposed action text
- `risk`: safety classification
- `allowed`: policy result
- `reason`: human-readable explanation
- `timestamp`: UTC ISO-8601 timestamp
- `status`: lifecycle status
- `correlation_id`: groups all events for one execution attempt
- `return_code`: process exit code when execution started
- `timed_out`: whether the execution exceeded its timeout
- `error`: bounded execution error description

## Execution lifecycle

A single controlled execution can produce:

`denied`

or:

`approved -> completed`

`approved -> failed`

`approved -> timed_out`

The executor creates one correlation ID before validating the action. That ID is reused for every audit event associated with the attempt.

The audit layer intentionally does not persist captured stdout/stderr. This avoids turning the local audit file into an uncontrolled sink for credentials, tokens, or other sensitive command output.

The logger records decisions and outcomes only. It does not execute commands, transmit data, or bypass approval gates.
