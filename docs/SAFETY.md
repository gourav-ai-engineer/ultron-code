# Safety Policy

ULTRON CODE evaluates actions before any future execution layer can run them.

## Defaults

- `dry_run=True`: actions are inspected but never executed.
- Destructive command patterns are blocked.
- Sensitive operations such as `git push`, package installation, Docker, and Terraform require approval.
- `emergency_stop=True` blocks all actions.
- Every decision includes an action, risk classification, reason, and UTC timestamp.

## Important boundary

This phase only evaluates actions. It does not execute shell commands, automate keyboards, control screens, or connect to external AI providers. Those capabilities must be added behind the safety policy and explicit user controls.
