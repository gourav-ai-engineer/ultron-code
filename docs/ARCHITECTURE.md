# ULTRON CODE Architecture

## High-Level Components

- **Control Plane:** project, phase, task, and approval state
- **Planner:** converts goals into structured phases and acceptance criteria
- **Observer:** collects screen, window, terminal, Git, and provider signals
- **Analyzer:** evaluates progress against acceptance criteria
- **Executor:** prepares and optionally submits the next instruction
- **Safety Layer:** approval gates, action limits, restricted paths, and emergency stop
- **Persistence:** stores state, events, prompts, responses, and validation results

## Execution Loop

1. Load the active project state.
2. Read the current phase acceptance criteria.
3. Collect signals from the repository and connected tools.
4. Analyze whether the phase is complete, blocked, or needs correction.
5. Run configured validation checks.
6. Generate the next action proposal.
7. Require approval when policy demands it.
8. Execute the approved action through an adapter.
9. Persist all events and repeat.

## Integration Strategy

Prefer official APIs, local process inspection, Git, and test results. Use screen capture and keyboard automation only when a supported direct integration is unavailable. Every action must be observable and interruptible.

## Initial Scope

The first milestone will implement project state models, a local phase controller, structured event logging, and a dry-run execution mode. Screen automation and external provider adapters will be added after the core state machine is tested.
