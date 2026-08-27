from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from aoic_kernel.models import LaunchGate, LaunchGateStatus


REQUIRED_GATES = [
    "legal_review",
    "licensing_review",
    "security_approval",
    "claims_review",
    "psp_agreement",
    "billing_ready",
    "support_ready",
    "public_track_record",
]


class CommercialReadiness:
    """Launch-gate registry for commercial readiness; all required gates must pass."""

    def __init__(self, required_gates: list[str] | None = None) -> None:
        self.required_gates = required_gates or list(REQUIRED_GATES)
        self._gates: dict[str, LaunchGate] = {}

    def submit_gate(
        self,
        name: str,
        status: LaunchGateStatus,
        reviewed_by: str,
        evidence: list[str] | None = None,
        expires_at: datetime | None = None,
    ) -> LaunchGate:
        gate = LaunchGate(
            gate_id=f"LG-{uuid.uuid4().hex[:12]}",
            name=name,
            status=status,
            evidence=evidence or [],
            reviewed_by=reviewed_by,
            reviewed_at=datetime.now(timezone.utc),
            expires_at=expires_at,
        )
        self._gates[name] = gate
        return gate

    def get(self, name: str) -> LaunchGate | None:
        return self._gates.get(name)

    def readiness(self) -> dict[str, Any]:
        missing = [g for g in self.required_gates if g not in self._gates]
        failed = [
            g for g in self.required_gates
            if g in self._gates and self._gates[g].status not in {LaunchGateStatus.PASSED, LaunchGateStatus.WAIVED}
        ]
        return {
            "ready": not missing and not failed,
            "missing": missing,
            "failed": failed,
            "passed": [g for g in self.required_gates if g in self._gates and self._gates[g].status == LaunchGateStatus.PASSED],
        }

    def is_ready(self) -> bool:
        return self.readiness()["ready"]
