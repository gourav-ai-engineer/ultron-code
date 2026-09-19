# Prompt Synthesis and UI Automation

The prompt synthesis layer converts observed state into a provider-facing instruction without calling an external model.

The interaction layer is intentionally separate from observation:

- `ProviderAdapter` is read-only.
- `ProviderInteractionAdapter` is write-capable.
- `InteractionGateway` requires explicit approval before a write.
- `KeyboardController` is disabled in dry-run mode and still passes through the safety policy.
- `ScreenObserver` captures a screenshot but does not click or type.

This separation lets ULTRON use official provider APIs where available and fall back to local screen/keyboard automation only when explicitly enabled.

No provider write adapter or keyboard action is triggered automatically by the synthesis engine.
