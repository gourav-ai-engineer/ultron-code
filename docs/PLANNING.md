# Planning Engine

ULTRON CODE currently uses a deterministic local planner. It converts a project name, goal, and optional technology hints into a structured `Project` containing ordered `Phase` objects.

## CLI

```bash
ultron plan --name "ULTRON CODE" --goal "Build an AI backend API" --technologies "FastAPI,RAG,PostgreSQL"
```

The plan is saved to `.ultron/project.json` by default. The planner does not call an external LLM, execute commands, or modify source files.

## Current behavior

- Always creates requirements/architecture, testing/validation, and deployment/documentation phases.
- Adds AI/ML, backend, or UI phases when matching keywords are present.
- Includes acceptance criteria for every phase.
- Produces stable, sequential phase IDs.

## Future extensions

1. Add a reviewed LLM planner behind an explicit provider interface.
2. Validate generated plans against a schema and safety policy.
3. Support user approval before replacing an existing plan.
4. Add dependency graphs, estimates, risks, and measurable verification commands.
