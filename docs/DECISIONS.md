# Decision Engine

The decision engine translates a `ProgressState` into an explainable recommendation.

## Decision types

- `wait`: progress is active; observe again later.
- `review`: evidence is incomplete or the provider is idle.
- `request_input`: the workflow is blocked and needs human input.
- `advance_phase`: completion and acceptance criteria indicate that the phase may advance.

## Safety boundary

This component only returns a structured recommendation. It does not send prompts, execute commands, mutate project state, or bypass approval gates. A future executor must validate every recommendation through the safety policy and audit logger.
