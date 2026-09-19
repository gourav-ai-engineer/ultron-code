from dataclasses import dataclass

from ultron.autonomous import AutonomousLoopConfig, AutonomousRunner
from ultron.interaction import InteractionResult
from ultron.providers import MockProvider
from ultron.workflow import WorkflowEngine
from ultron.workspace import WorkspaceObserver


@dataclass
class FakeInteraction:
    sent: list[str]

    @property
    def provider(self) -> str:
        return "mock"

    def send_prompt(self, prompt, correlation_id, approval=None, requires_approval=True):
        self.sent.append(prompt)
        return InteractionResult("i-1", self.provider, True, "sent", correlation_id)


def test_autonomous_runner_dispatches_when_enabled(tmp_path) -> None:
    interaction = FakeInteraction([])
    runner = AutonomousRunner(
        WorkflowEngine(WorkspaceObserver(tmp_path)),
        MockProvider(summary="Working", progress=0.5),
        interaction=interaction,
        config=AutonomousLoopConfig(max_iterations=1, auto_prompt_enabled=True),
    )

    cycles = runner.run(lambda: True)

    assert len(cycles) == 1
    assert cycles[0].delivery is not None
    assert cycles[0].delivery.interaction.accepted is True
    assert interaction.sent


def test_autonomous_runner_does_not_dispatch_in_default_mode(tmp_path) -> None:
    interaction = FakeInteraction([])
    runner = AutonomousRunner(
        WorkflowEngine(WorkspaceObserver(tmp_path)),
        MockProvider(summary="Working", progress=0.5),
        interaction=interaction,
        config=AutonomousLoopConfig(max_iterations=1),
    )

    cycles = runner.run(lambda: True)

    assert cycles[0].delivery is None
    assert interaction.sent == []
