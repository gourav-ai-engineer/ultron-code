from ultron.models import Phase, PhaseStatus, Project
from ultron.orchestrator import Orchestrator


def make_project() -> Project:
    return Project(
        name="Demo",
        goal="Validate orchestration",
        phases=[
            Phase(id="phase-1", title="Setup", objective="Create setup"),
            Phase(id="phase-2", title="Testing", objective="Run tests"),
        ],
    )


def test_start_and_complete_phase() -> None:
    project = make_project()
    orchestrator = Orchestrator(project)

    phase = orchestrator.start_next_phase()
    assert phase is not None
    assert phase.id == "phase-1"
    assert phase.status == PhaseStatus.ACTIVE

    orchestrator.complete_active_phase()
    assert project.phases[0].status == PhaseStatus.COMPLETED
    assert project.active_phase_id is None


def test_next_pending_phase() -> None:
    orchestrator = Orchestrator(make_project())
    assert orchestrator.next_pending_phase().id == "phase-1"
