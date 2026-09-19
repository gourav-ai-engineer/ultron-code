from ultron.models import PhaseStatus
from ultron.planner import ProjectPlanner


def test_planner_creates_ai_backend_plan() -> None:
    project = ProjectPlanner().create_plan(
        name="Demo",
        goal="Build an AI backend API",
        technologies=["FastAPI", "RAG"],
    )

    titles = [phase.title for phase in project.phases]
    assert "AI/ML Pipeline" in titles
    assert "Backend Implementation" in titles
    assert project.phases[0].status == PhaseStatus.PENDING
    assert project.phases[0].acceptance_criteria


def test_planner_creates_minimum_plan() -> None:
    project = ProjectPlanner().create_plan("Demo", "Build a utility")
    assert len(project.phases) == 3
    assert project.phases[-1].title == "Deployment and Documentation"
