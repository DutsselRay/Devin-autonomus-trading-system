from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from aoic_kernel.models import RedTeamExercise


class RedTeam:
    """External red-team exercise registry."""

    def __init__(self) -> None:
        self._exercises: dict[str, RedTeamExercise] = {}

    def plan(self, target_system: str, objective: str, team: list[str]) -> RedTeamExercise:
        if not team:
            raise ValueError("red team exercise requires a team")
        exercise = RedTeamExercise(
            exercise_id=f"RT-{uuid4().hex[:8].upper()}",
            target_system=target_system,
            objective=objective,
            team=team,
        )
        self._exercises[exercise.exercise_id] = exercise
        return exercise

    def get(self, exercise_id: str) -> RedTeamExercise:
        if exercise_id not in self._exercises:
            raise KeyError(exercise_id)
        return self._exercises[exercise_id]

    def list_exercises(self) -> list[RedTeamExercise]:
        return list(self._exercises.values())

    def start(self, exercise_id: str) -> RedTeamExercise:
        exercise = self.get(exercise_id)
        if exercise.status != "PLANNED":
            raise ValueError("exercise must be PLANNED to start")
        exercise.status = "RUNNING"
        exercise.started_at = datetime.now(timezone.utc)
        self._exercises[exercise_id] = exercise
        return exercise

    def complete(self, exercise_id: str, findings: list[str]) -> RedTeamExercise:
        exercise = self.get(exercise_id)
        if exercise.status != "RUNNING":
            raise ValueError("exercise must be RUNNING to complete")
        exercise.status = "COMPLETED"
        exercise.completed_at = datetime.now(timezone.utc)
        exercise.findings.extend(findings)
        self._exercises[exercise_id] = exercise
        return exercise
