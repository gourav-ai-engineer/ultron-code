# Audit Trail

ULTRON CODE records safety decisions as JSON Lines in `.ultron/audit.jsonl`.

Each event contains:

- `event_id`: unique event identifier
- `action`: proposed action text
- `risk`: safety classification
- `allowed`: policy result
- `reason`: human-readable explanation
- `timestamp`: UTC ISO-8601 timestamp
- `status`: lifecycle status
- `correlation_id`: groups events within one workflow run

The logger only records decisions. It does not execute commands, transmit data, or bypass approval gates.
