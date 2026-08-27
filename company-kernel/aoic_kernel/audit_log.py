from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from aoic_kernel.models import AuditEntry


class ImmutableAuditLog:
    """Append-only, hash-chained audit log."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def _hash_entry(self, entry: AuditEntry, previous_hash: str | None) -> str:
        payload = {
            "entry_id": entry.entry_id,
            "timestamp": entry.timestamp.isoformat(),
            "event_type": entry.event_type,
            "actor": entry.actor,
            "action": entry.action,
            "target": entry.target,
            "outcome": entry.outcome,
            "details": entry.details,
            "previous_hash": previous_hash,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()

    def append(
        self,
        entry_id: str,
        event_type: str,
        actor: str,
        action: str,
        target: str,
        outcome: str,
        details: dict[str, Any] | None = None,
    ) -> AuditEntry:
        previous_hash = self._entries[-1].hash if self._entries else None
        entry = AuditEntry(
            entry_id=entry_id,
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            actor=actor,
            action=action,
            target=target,
            outcome=outcome,
            details=details or {},
            previous_hash=previous_hash,
        )
        entry.hash = self._hash_entry(entry, previous_hash)
        self._entries.append(entry)
        return entry

    @property
    def entries(self) -> list[AuditEntry]:
        return list(self._entries)

    def verify(self) -> bool:
        for i, entry in enumerate(self._entries):
            prev_hash = self._entries[i - 1].hash if i > 0 else None
            expected = self._hash_entry(entry, prev_hash)
            if entry.hash != expected:
                return False
            if i > 0 and entry.previous_hash != self._entries[i - 1].hash:
                return False
        return True
