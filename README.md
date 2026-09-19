# ULTRON CODE

**Hybrid autonomous AI development orchestrator**

ULTRON CODE coordinates an AI-assisted software-development workflow across project planning, provider observation, workspace monitoring, progress analysis, next-prompt synthesis, controlled execution, desktop automation, and persistent audit/recovery.

## What is implemented

`Goal -> Plan -> Observe -> Correlate -> Decide -> Synthesize -> Approve/Trust -> Deliver/Execute -> Audit -> Repeat`

The current implementation includes:

- persistent project and phase state
- deterministic planning and acceptance criteria
- read-only provider adapters for OpenAI Responses, Anthropic Models API, and Cursor Cloud Agent runs
- free-first model inference through Gemini, OpenRouter's free-model router, and local Ollama
- screen/OCR observation for ChatGPT, Claude, and Cursor desktop windows
- Git/workspace observation
- progress correlation and explainable decisions
- deterministic next-prompt synthesis
- human approval requests with correlation binding
- restricted local command execution
- execution timeouts and output capture
- JSONL audit history with execution outcomes
- workflow run persistence and rehydration
- pause, resume, and persistent emergency-stop controls
- bounded observation loops
- explicit autonomous prompt-dispatch mode
- local FastAPI control plane and dashboard
- Docker packaging
- CI configuration for Python 3.11–3.14

## Original ULTRON use case

For a desktop AI tool such as ChatGPT, the screen-backed path can:

1. focus the configured AI window
2. capture the current screen
3. OCR the visible response
4. correlate the response with repository activity
5. decide what should happen next
6. synthesize the next instruction
7. optionally type and submit that instruction
8. repeat under a bounded loop and persistent stop controls

Automatic prompt delivery is disabled by default.

## Installation

Core:

`python -m pip install -e ".[dev]"`

API/dashboard:

`python -m pip install -e ".[api]"`

Desktop automation:

`python -m pip install -e ".[automation,ocr]"`

Free-first model clients use only the Python standard library; no extra model SDK is required.

When `--reasoner gemini` is used with `workflow-run` or `auto-loop`, Gemini provides advisory reasoning for REVIEW decisions. Its output is included as evidence in the next prompt; it never bypasses ULTRON safety or execution controls.

The OCR path also requires the Tesseract executable to be installed on the machine. Configure `ULTRON_TESSERACT_CMD` when it is not available on PATH.

## Configuration

Copy `.env.example` to `.env` and configure only the capabilities you need.

Safe defaults:

`ULTRON_DRY_RUN=true`

`ULTRON_AUTOMATION_ENABLED=false`

`ULTRON_AUTO_PROMPT_ENABLED=false`

## Basic workflow

Initialize and plan:

`ultron init`

`ultron plan`

Activate a phase:

`ultron next-phase`

Observe with an offline provider:

`ultron workflow-run --provider mock --provider-summary "Working" --progress 0.5`

Observe a real OpenAI Responses API response:

`ultron workflow-run --provider chatgpt --response-id <response-id>`

Observe a Cursor Cloud Agent run:

`ultron workflow-run --provider cursor --agent-id <agent-id> --provider-run-id <run-id>`

Observe a desktop ChatGPT window:

`ultron workflow-run --provider screen-chatgpt --screen-window-title "ChatGPT"`

### Free model providers

Gemini is the recommended cloud provider for this setup. Google currently lists a free tier for Gemini 3.8 Flash, with free input and output tokens subject to the model's free-tier limits. Create the key in Google AI Studio and set `GEMINI_API_KEY`.

Run Gemini:

`ultron provider-generate --provider gemini --prompt "Review the current project goal and propose the next implementation step."`

OpenRouter can route to currently available free models with `openrouter/free`; its free plan currently lists 25+ free models and a 50-request/day limit. Set `OPENROUTER_API_KEY`.

Run OpenRouter free routing:

`ultron provider-generate --provider openrouter --prompt "Review the current project goal and propose the next implementation step."`

Ollama is the no-cloud-cost option. Install Ollama locally, pull a model, set `OLLAMA_MODEL`, and run:

`ultron provider-generate --provider ollama --prompt "Review the current project goal and propose the next implementation step."`
## Autonomous desktop mode

Enable explicitly:

`ULTRON_DRY_RUN=false`

`ULTRON_AUTOMATION_ENABLED=true`

`ULTRON_AUTO_PROMPT_ENABLED=true`

Then run:

`ultron auto-loop --provider screen-chatgpt --screen-window-title "ChatGPT"`

Only workflow decisions that do not require human input are automatically dispatched. Blocked states and phase-advance decisions remain outside the autonomous dispatch path.

Use:

`ultron control-stop`

to trigger the persistent emergency stop.

## Controlled execution

Dry-run:

`ultron execute --action "git status"`

Live execution:

`ultron execute --action "git status" --live`

Write-capable or destructive operations are restricted by the safety policy and command allowlist.

## Control plane

Start the local API:

`ultron serve`

The dashboard is available from the local server at `/dashboard/`.

The HTTP API supports health, provider inventory, workflow-run history, observation, and operator control endpoints.

## Project layout

```
src/ultron/
├── models.py              # project/phase models
├── planner.py             # deterministic planning
├── orchestrator.py        # phase transitions
├── state.py               # project persistence
├── providers.py           # provider protocol
├── provider_runtime.py    # OpenAI/Anthropic/Cursor observers
├── provider_registry.py   # provider factory
├── workspace.py           # Git/workspace observation
├── correlation.py         # progress classification
├── decision.py            # next-action decisions
├── synthesis.py           # next-prompt generation
├── reasoning.py           # Gemini advisory reasoning
├── approval.py            # human approval lifecycle
├── safety.py              # policy and emergency-stop checks
├── executor.py            # restricted subprocess execution
├── audit.py               # persistent audit trail
├── workflow.py             # end-to-end run graph
├── run_store.py            # run persistence/rehydration
├── autonomous.py            # autonomous prompt dispatch loop
├── interaction.py           # provider write contract
├── delivery.py              # prompt delivery service
├── automation.py            # screen/keyboard controls
├── desktop.py               # Windows desktop adapter
├── screen_reader.py         # OCR
├── screen_provider.py       # screen-backed observation
├── control.py               # pause/stop state
├── loop.py                  # bounded observation loop
├── recovery.py              # restart/recovery state
├── validator.py              # validation runner
├── runtime.py                # runtime facade
└── api.py                    # local HTTP control plane
```

## Safety model

ULTRON CODE is intentionally layered:

`observe -> decide -> approve/trust -> execute/deliver -> audit`

No component is allowed to bypass the safety layer. UI automation is disabled by default, shell execution is allowlisted, workspace paths are constrained, and emergency-stop state is persistent.

## Verification status

The implementation pass is complete. The automated test suite and runtime verification have **not** been executed yet, intentionally, so the repository can be tested as one complete system in the next step.
