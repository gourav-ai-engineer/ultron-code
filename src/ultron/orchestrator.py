"""Phase orchestration logic for ULTRON CODE."""

from .models import PhaseStatus, Project


class Orchestrator:
    """Manage phase transitions without executing external actions."""

    def __init__(self, project: Project) -> None:
        self.project = project

    def next_pending_phase(self):
        """Return the first pending phase, if one exists."""
        return next(
            (phase for phase in self.project.phases if phase.status == PhaseStatus.PENDING),
            None,
        )

    def start_next_phase(self):
        """Activate the next pending phase and return it."""
        phase = self.next_pending_phase()
        if phase is None:
            return None
        phase.status = PhaseStatus.ACTIVE
        self.project.active_phase_id = phase.id
        return phase

    def complete_active_phase(self) -> None:
        """Complete the active phase."""
        if self.project.active_phase_id is None:
            raise RuntimeError("No active phase to complete")

        for phase in self.project.phases:
            if phase.id == self.project.active_phase_id:
                phase.status = PhaseStatus.COMPLETED
                self.project.active_phase_id = None
                return

        raise RuntimeError("Active phase ID does not exist in the project")
