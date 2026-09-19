"""Core domain models for projects and execution phases."""

from enum import StrEnum

from pydantic import BaseModel, Field


class PhaseStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"


class Phase(BaseModel):
    id: str
    title: str
    objective: str
    acceptance_criteria: list[str] = Field(default_factory=list)
    status: PhaseStatus = PhaseStatus.PENDING


class Project(BaseModel):
    name: str
    goal: str
    phases: list[Phase] = Field(default_factory=list)
    active_phase_id: str | None = None
