# Provider Registry

Phase 15 adds a single registry for selecting runtime provider adapters.

## Registered providers

- `mock`: deterministic local provider for tests and offline workflows
- `chatgpt`: OpenAI Responses API adapter
- `claude`: Anthropic Models API adapter
- `cursor`: Cursor Cloud Agent run adapter

The registry accepts a provider enum or string and constructs the matching adapter without exposing provider-specific branching to the workflow engine.

## Workflow integration

The `workflow-run` CLI now accepts a provider selection. Example:

`ultron workflow-run --provider chatgpt --response-id <response-id>`

`ultron workflow-run --provider claude`

`ultron workflow-run --provider cursor --agent-id <agent-id> --provider-run-id <run-id>`

For offline development:

`ultron workflow-run --provider mock --provider-summary "Working" --progress 0.5`

## Safety boundary

The registry only constructs adapters. It does not send prompts or execute actions. Real provider snapshots still flow through the Phase 13 workflow engine, while any execution remains behind the existing safety and approval gates.
