from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from aoic_kernel.models import ApprovalRecord, Authority, DecisionProposal
from aoic_kernel.exceptions import ApprovalExpired


class ApprovalEngine:
    """Records explicit, scoped, expiring approvals."""

    def __init__(self) -> None:
        self._approvals: dict[str, ApprovalRecord] = {}

    def request(
        self,
        approval_id: str,
        decision_id: str,
        approver: str,
        authority: Authority,
        expires_at: Optional[datetime] = None,
        scope: str = "",
    ) -> ApprovalRecord:
        record = ApprovalRecord(
            approval_id=approval_id,
            decision_id=decision_id,
            approver=approver,
            authority=authority,
            granted_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            scope=scope,
        )
        self._approvals[approval_id] = record
        return record

    def validate(self, approval_id: str, decision_id: str) -> ApprovalRecord:
        if approval_id not in self._approvals:
            raise ApprovalExpired(f"Approval {approval_id} not found")
        record = self._approvals[approval_id]
        if record.decision_id != decision_id:
            raise ApprovalExpired("Approval does not match decision")
        if record.revoked:
            raise ApprovalExpired("Approval has been revoked")
        if record.expires_at and datetime.now(timezone.utc) > record.expires_at:
            raise ApprovalExpired("Approval has expired")
        return record

    def revoke(self, approval_id: str) -> None:
        if approval_id in self._approvals:
            self._approvals[approval_id].revoked = True
