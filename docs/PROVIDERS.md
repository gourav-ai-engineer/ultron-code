# Provider Adapter Architecture

ULTRON CODE uses a provider-neutral, read-only adapter contract.

## Contract

Each provider adapter exposes:

- `provider`: provider identity
- `health_check()`: local connection/availability status
- `snapshot()`: current session summary and optional progress

## Safety boundary

This phase does not send prompts, execute commands, automate keyboards, or control browser sessions. Future write-capable adapters must pass through the safety policy, approval gates, and audit logger.

## Implementations

`MockProvider` is included for deterministic development and testing. ChatGPT, Claude, and Cursor are represented as provider kinds but require dedicated, explicitly authorized integrations in later phases.
