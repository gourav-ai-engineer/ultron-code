# ULTRON Runtime

The runtime layer provides:

- `PromptSynthesizer` for provider-facing next instructions
- `ProviderInteractionAdapter` for explicit provider writes
- `ScreenObserver` and `KeyboardController` for optional UI fallback
- `WorkflowLoop` for bounded repeated observation
- `RunStore` for persistent workflow history
- `UltronSettings` for environment-backed configuration
- security helpers for workspace confinement and common-secret redaction

Safe defaults remain authoritative:

- dry-run is enabled by default
- UI automation is disabled by default
- loop iterations can be bounded
- workspace paths are validated
- provider writes require explicit approval through the interaction gateway

This runtime does not silently run forever or implicitly send prompts to external providers.
