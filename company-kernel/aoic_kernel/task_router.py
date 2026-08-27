from __future__ import annotations

from typing import Any, Callable

from aoic_kernel.models import AOICEvent


class TaskRouter:
    """Ownership, priority, deadlines, retries and dead-letter handling."""

    def __init__(self) -> None:
        self._tasks: list[dict[str, Any]] = []
        self._routes: dict[str, Callable[[dict[str, Any]], None]] = {}

    def register_route(self, task_type: str, handler: Callable[[dict[str, Any]], None]) -> None:
        self._routes[task_type] = handler

    def submit(self, task: dict[str, Any]) -> dict[str, Any]:
        task.setdefault("retries", 0)
        task.setdefault("status", "PENDING")
        self._tasks.append(task)
        return task

    def dispatch(self, event: AOICEvent) -> None:
        task_type = event.payload.get("task_type")
        if task_type in self._routes:
            self._routes[task_type](event.payload)

    @property
    def pending(self) -> list[dict[str, Any]]:
        return [t for t in self._tasks if t["status"] == "PENDING"]
