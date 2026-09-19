# Provider Feedback Correlation

The correlation layer combines a provider snapshot with a read-only workspace snapshot.

## States

- `progressing`: file activity or positive reported progress exists.
- `idle`: a session exists but no progress signal was detected.
- `blocked`: the provider summary contains a blocking signal such as `blocked`, `error`, or `failed`.
- `complete`: the provider reports progress of `1.0` or higher.
- `unknown`: insufficient signals are available.

This component is deterministic and does not send prompts, modify files, or execute external actions. Its output must be reviewed before future automation decisions.
