"""Validation command runner for ULTRON CODE."""

from dataclasses import dataclass

from .executor import ActionExecutor, ExecutionResult


@dataclass(frozen=True)
class ValidationReport:
    """Structured result of configured validation commands."""

    passed: bool
    results: tuple[ExecutionResult, ...]


class Validator:
    """Run only the executor's approved developer validation commands."""

    def __init__(self, executor: ActionExecutor) -> None:
        self.executor = executor

    def validate(self, commands: tuple[str, ...]) -> ValidationReport:
        results: list[ExecutionResult] = []
        for command in commands:
            results.append(self.executor.execute(command))
            result = results[-1]
            if result.timed_out or result.return_code != 0:
                return ValidationReport(False, tuple(results))
        return ValidationReport(True, tuple(results))
