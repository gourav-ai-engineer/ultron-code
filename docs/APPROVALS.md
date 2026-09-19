# Human Approval Gateway

The approval gateway is the control point between ULTRON CODE's recommendations and any future write-capable executor.

## Approval lifecycle

`pending -> approved`

`pending -> rejected`

`pending -> deferred`

Only a pending request can be resolved. The gateway never executes the requested action.

## Safety relationship

An approval request can only be created from a `SafetyDecision` whose risk is `requires_approval`.

Blocked actions cannot be approved through this layer. Dry-run mode and the emergency stop remain authoritative.

## Persistence

Requests are stored locally in `.ultron/approvals.json`. Each request has:

- a unique request ID
- requested action
- rationale
- risk classification
- current approval status
- request and resolution timestamps
- optional resolution note
- correlation ID

This record can later be connected to the audit stream and a UI without changing the safety boundary.
