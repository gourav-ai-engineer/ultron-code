# End-to-End Workflow Runs

Phase 13 introduces the workflow integration contract.

## Workflow

A run follows:

`provider snapshot -> workspace snapshot -> progress correlation -> decision -> optional controlled execution`

Every run receives a unique `run_id`. When execution is requested, that same ID becomes the executor's correlation ID and therefore links the execution audit records back to the original observation.

## Boundaries

The workflow engine:

- reads provider state through the existing `ProviderAdapter` contract
- observes workspace state through `WorkspaceObserver`
- delegates progress classification to `ProgressCorrelator`
- delegates recommendations to `DecisionEngine`
- delegates execution to `ActionExecutor`
- does not bypass safety policy or approval checks
- does not automatically invent or send provider prompts

Execution is explicit: a caller must supply the action, and the configured executor still applies its allowlist, safety policy, and approval requirements.

## Why this matters

Future provider integrations can focus on translating a real ChatGPT, Claude, or Cursor session into `ProviderSnapshot` data. The orchestration layer remains provider-neutral.
