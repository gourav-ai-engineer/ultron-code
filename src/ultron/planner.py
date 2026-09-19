"""Deterministic project planning for ULTRON CODE."""

from collections.abc import Sequence

from .models import Phase, Project


class ProjectPlanner:
    """Create a predictable baseline plan without external model calls."""

    def create_plan(
        self,
        name: str,
        goal: str,
        technologies: Sequence[str] | None = None,
    ) -> Project:
        """Build a project with phases selected from the goal and technology hints."""
        hints = " ".join(technologies or ()).lower()
        text = f"{goal} {hints}".lower()
        phases = [
            Phase(
                id="phase-1",
                title="Requirements and Architecture",
                objective="Clarify scope, constraints, interfaces, and system architecture.",
                acceptance_criteria=["Scope and constraints are documented", "Architecture is reviewed"],
            )
        ]

        if any(term in text for term in ("ai", "ml", "llm", "model", "rag")):
            phases.append(
                Phase(
                    id=f"phase-{len(phases) + 1}",
                    title="AI/ML Pipeline",
                    objective="Define data, model, evaluation, and inference workflows.",
                    acceptance_criteria=["Data and model interfaces are defined", "Evaluation criteria are measurable"],
                )
            )
        if any(term in text for term in ("api", "backend", "fastapi", "service")):
            phases.append(
                Phase(
                    id=f"phase-{len(phases) + 1}",
                    title="Backend Implementation",
                    objective="Implement the core service interfaces and business logic.",
                    acceptance_criteria=["Core endpoints or service interfaces work", "Input validation is covered"],
                )
            )
        if any(term in text for term in ("frontend", "web", "ui", "dashboard")):
            phases.append(
                Phase(
                    id=f"phase-{len(phases) + 1}",
                    title="User Interface",
                    objective="Implement the user-facing workflow and error states.",
                    acceptance_criteria=["Primary user workflow is usable", "Loading and error states are handled"],
                )
            )
        phases.extend(
            [
                Phase(
                    id=f"phase-{len(phases) + 1}",
                    title="Testing and Validation",
                    objective="Add automated tests and verify the acceptance criteria.",
                    acceptance_criteria=["Automated tests pass", "Acceptance criteria are verified"],
                ),
                Phase(
                    id=f"phase-{len(phases) + 1}",
                    title="Deployment and Documentation",
                    objective="Prepare reproducible deployment and operator documentation.",
                    acceptance_criteria=["Deployment steps are documented", "Operational risks are recorded"],
                ),
            ]
        )
        return Project(name=name, goal=goal, phases=phases)
