# Provider Runtime Adapters

Phase 14 adds concrete, read-only runtime adapters behind the existing `ProviderAdapter` protocol.

## OpenAI / ChatGPT

`OpenAIResponseAdapter` reads a specific OpenAI Responses API response by ID using `OPENAI_API_KEY` or an explicitly supplied key.

This is an API-runtime adapter. It does **not** claim access to a user's private ChatGPT web-app conversation history.

## Claude

`AnthropicModelsAdapter` checks the Claude API through `GET /v1/models` and exposes API availability/model-count information as a provider snapshot.

Anthropic's documented Models API is an API catalog endpoint; this adapter therefore does **not** pretend that it can read a consumer Claude.app conversation.

## Cursor

`CursorCloudRunAdapter` reads a specific Cursor Cloud Agent run using the Cloud Agents API. Cursor documents run-level status, result text, and run IDs in its public API.

Cursor's current Cloud Agents API is public beta and may change; the adapter keeps the endpoint and response parsing isolated for that reason.

## Secrets

API keys are accepted directly or read from environment variables:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `CURSOR_API_KEY`

Keys are never placed in provider snapshots or audit records.

## Safety boundary

These adapters are read-only. They do not send prompts, execute code, create agents, or modify repositories.

The next integration can add an explicit provider registry and connect these snapshots to the Phase 13 workflow engine.

## Verified current integration surfaces

OpenAI's current API platform exposes programmatic agent workflows through the Responses API. citeturn235760search2

Anthropic documents `GET /v1/models` as its Models API endpoint. citeturn514294view1

Cursor documents Cloud Agents as a programmatic API and documents `GET /v1/agents/{id}/runs/{runId}` for run state/result retrieval. citeturn685454search0
