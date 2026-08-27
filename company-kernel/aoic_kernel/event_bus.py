from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from aoic_kernel.models import AOICEvent


class EventBus:
    """Typed, durable, idempotent events."""

    def __init__(self) -> None:
        self._events: list[AOICEvent] = []
        self._handlers: dict[str, list[Callable[[AOICEvent], None]]] = {}

    def publish(
        self,
        event_type: str,
        source: str,
        payload: dict[str, Any],
        event_id: str | None = None,
        causality: dict[str, Any] | None = None,
    ) -> AOICEvent:
        event = AOICEvent(
            event_id=event_id or f"EVT-{len(self._events) + 1:06d}",
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            source=source,
            payload=payload,
            causality=causality,
        )
        self._events.append(event)
        for handler in self._handlers.get(event_type, []):
            handler(event)
        for handler in self._handlers.get("*", []):
            handler(event)
        return event

    def subscribe(self, event_type: str, handler: Callable[[AOICEvent], None]) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    @property
    def events(self) -> list[AOICEvent]:
        return list(self._events)

    def events_of_type(self, event_type: str) -> list[AOICEvent]:
        return [e for e in self._events if e.event_type == event_type]
