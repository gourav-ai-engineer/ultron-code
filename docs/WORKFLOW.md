# End-to-End Workflow Runs

Phase 13 introduced the workflow integration contract. Phase 15 connects it to the provider registry.

## Workflow

A run follows:

`provider snapshot -> workspace snapshot -> progress correlation -> decision -> optional controlled execution`

Every run receives a unique `run_id`. When execution is requested, that same ID becomes the executor's correlation ID and therefore links the execution audit records back to the original observation.

## Provider selection

The workflow CLI resolves a provider through `ProviderRegistry`.

A mock/offline observation:

`ultron workflow-run --provider mock --provider-summary "Working" --progress 0.5`

An OpenAI Responses API observation:

`ultron workflow-run --provider chatgpt --response-id <response-id>`

A Claude API availability observation:

`ultron workflow-run --provider claude`

A Cursor Cloud Agent run observation:

`ultron workflow-run --provider cursor --agent-id <agent-id> --provider-run-id <run-id>`

Only the provider adapter knows how to contact the external service. The workflow engine remains provider-neutral.

## Execution

An explicitly supplied action can be evaluated through the same run:

`ultron workflow-run --provider mock --workspace . --action "git status"`

Live execution still requires the existing `--live` flag and any approval required by the safety policy.

## Boundaries

The workflow engine:

- reads provider state through the existing `ProviderAdapter` contract
- observes workspace state through `WorkspaceObserver`
- delegates progress classification to `ProgressCorrelator`
- delegates recommendations to `DecisionEngine`
- delegates execution to `ActionExecutor`
- does not bypass safety policy or approval checks
- does not automatically invent or send provider prompts

Provider registry selection likewise only constructs adapters; it does not execute provider actions.

## Why this matters

ULTRON can now switch providers without changing the orchestration graph. Future provider adapters can be added through the registry, while the safety and execution boundaries remain centralized.
