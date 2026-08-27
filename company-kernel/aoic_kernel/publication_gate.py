from __future__ import annotations

from datetime import datetime
from typing import Any

from aoic_kernel.models import DecisionProposal, PITRecord, RiskLevel
from aoic_kernel.policy_engine import PolicyEngine
from aoic_kernel.audit_log import ImmutableAuditLog
from aoic_kernel.exceptions import PublicationGateBlocked, PITViolation


class PublicationGate:
    """Research publication gate simulator."""

    PROBABILITY_GATE = 0.90

    def __init__(self, policy: PolicyEngine, audit: ImmutableAuditLog) -> None:
        self.policy = policy
        self.audit = audit

    def evaluate(
        self,
        proposal: DecisionProposal,
        pit_records: list[PITRecord],
        as_of: datetime,
        source_rights: dict[str, bool],
    ) -> str:
        """Return 'PASS' or raise PublicationGateBlocked with reason."""
        reasons: list[str] = []

        if proposal.confidence is None or proposal.confidence <= self.PROBABILITY_GATE:
            reasons.append(f"probability {proposal.confidence} not above gate {self.PROBABILITY_GATE}")

        for evidence in proposal.evidence:
            if evidence.source not in source_rights or not source_rights[evidence.source]:
                reasons.append(f"missing source rights for {evidence.source}")

        for record in pit_records:
            if record.released_at > as_of:
                reasons.append(f"PIT violation: record {record.record_id} released after as_of")

        if reasons:
            msg = "; ".join(reasons)
            self.audit.append(
                entry_id=f"AUD-{len(self.audit.entries)+1:06d}",
                event_type="PUBLICATION_BLOCKED",
                actor="publication_gate",
                action="evaluate",
                target=proposal.decision_id,
                outcome="BLOCK",
                details={"reasons": reasons},
            )
            raise PublicationGateBlocked(msg)

        self.audit.append(
            entry_id=f"AUD-{len(self.audit.entries)+1:06d}",
            event_type="PUBLICATION_PASSED",
            actor="publication_gate",
            action="evaluate",
            target=proposal.decision_id,
            outcome="PASS",
            details={},
        )
        return "PASS"
