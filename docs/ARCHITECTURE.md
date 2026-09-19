# ULTRON CODE Architecture

## System goal

ULTRON CODE is a local control plane for AI-assisted software development.

It combines structured project state, multiple observation channels, deterministic analysis, explicit safety gates, controlled execution, optional desktop automation, and persistent evidence.

## End-to-end graph

`Project Goal
  -> Planner
  -> Active Phase
  -> Provider/Workspace Observation
  -> Progress Correlator
  -> Decision Engine
  -> Prompt Synthesizer
  -> Approval or Trusted Automation
  -> Provider Interaction / Action Executor
  -> Audit + Run Store
  -> Next Observation`

## Layers

### 1. Project layer

`models.py`, `planner.py`, `state.py`, and `orchestrator.py` manage:

- project goal
- ordered phases
- acceptance criteria
- active phase
- phase transitions

Phase transitions remain explicit and do not run external commands.

### 2. Observation layer

Provider observation is normalized into `ProviderSnapshot`.

Supported API-backed observations:

- OpenAI Responses API
- Anthropic Models API
- Cursor Cloud Agent runs

Supported UI-backed observations:

- ChatGPT desktop/web window
- Claude desktop/web window
- Cursor desktop window

Workspace observation is performed independently through read-only Git inspection.

### 3. Correlation layer

`ProgressCorrelator` combines provider signals and workspace changes into:

- progressing
- idle
- blocked
- complete
- unknown

### 4. Decision layer

`DecisionEngine` produces explainable recommendations:

- wait
- review
- request_input
- advance_phase

The decision engine does not execute the recommendation.

### 5. Synthesis layer

`PromptSynthesizer` converts the evidence and decision into a provider-facing instruction.

Prompt content is secret-redacted before it enters persistent workflow history.

### 6. Safety layer

`SafetyPolicy`, `ApprovalGateway`, and `ControlStore` define the execution boundary.

Important invariants:

- dry-run is the default
- destructive patterns are blocked
- risky commands can require explicit approval
- emergency stop is persistent
- approvals are correlated to workflow runs
- keyboard automation requires either an approved request or an explicitly enabled trusted automation mode

### 7. Execution layer

`ActionExecutor` provides a restricted subprocess boundary:

- `shell=False`
- command allowlist
- workspace confinement
- timeout
- stdout/stderr capture
- structured result
- correlation ID
- execution audit events

It is intentionally not a generic shell.

### 8. Interaction layer

`ProviderInteractionAdapter` is separate from `ProviderAdapter`.

This keeps read access independent from write access.

`PromptDeliveryService` connects synthesized prompts to provider interaction adapters and persists delivery outcomes without storing prompt content in the audit trail.

### 9. Desktop fallback

`ScreenProviderAdapter` captures visible provider output through screenshots and optional OCR.

`DesktopProviderAdapter` can focus a window, type the synthesized prompt, and submit it.

Both are disabled unless explicitly enabled.

### 10. Runtime layer

`WorkflowLoop` provides bounded observation.

`AutonomousRunner` provides:

`observe -> synthesize -> safe dispatch -> observe again`

Automatic dispatch is limited to decisions that do not require human input.

### 11. Persistence

The runtime persists:

- project state
- approval requests
- workflow runs
- audit events
- control state

Run data is rehydratable by workflow run ID.

Common API credentials and recognizable token patterns are redacted before persistent logging.

### 12. API and dashboard

`api.py` exposes a local FastAPI control plane.

Default binding is loopback.

The dashboard under `web/` provides a lightweight runtime view over the API.

## Provider strategy

The orchestration core never branches on provider-specific APIs.

Provider-specific behavior lives behind adapters and the registry.

This means adding a new provider requires:

1. an observation adapter
2. optionally a write adapter
3. registration/configuration
4. tests for its mapping into `ProviderSnapshot`

The rest of ULTRON remains unchanged.

## Failure and recovery

Every controlled execution has a correlation ID.

Every workflow run has a run ID.

The same identifier connects:

- observation
- prompt synthesis
- approval requests
- execution audit records
- interaction audit records

The recovery manager uses persisted run history together with persistent control state to decide whether a session may be resumed.

## Deployment modes

### Local developer mode

Python CLI + optional desktop automation.

### Local control-plane mode

FastAPI + dashboard + Python runtime.

### Container mode

Docker image with the API/control plane. Desktop automation remains a host capability rather than a container assumption.

## Security boundary

ULTRON is intentionally designed so that the most capable path also has the most explicit controls:

`observe -> understand -> decide -> approve/trust -> act -> audit`

No provider adapter is granted implicit shell access, and no workflow run can silently bypass the control plane.
