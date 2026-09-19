# Provider Adapter Architecture

ULTRON CODE uses provider-neutral observation and interaction boundaries.

## Observation contract

Each workflow observation adapter exposes:

- `provider`: provider identity
- `health_check()`: connection/availability status
- `snapshot()`: current session summary and optional progress

## Free-first model inference

ULTRON also includes a separate inference layer for generating text with:

- **Gemini** — default cloud provider, configured with `GEMINI_API_KEY`
- **OpenRouter free router** — configured with `OPENROUTER_API_KEY` and `openrouter/free`
- **Ollama** — local inference with no cloud API key

The CLI command is:

`ultron provider-generate --provider gemini --prompt "..." `

Use `--model` to override the default model.

## Paid/desktop providers

OpenAI, Anthropic, and Cursor support remains available for existing observation/desktop paths, but none of their API keys are required for the free-first setup.

## Safety boundary

Model generation does not itself execute shell commands or type into desktop applications. Prompt delivery and command execution remain behind ULTRON's existing safety, approval, audit, workspace, and emergency-stop controls.
