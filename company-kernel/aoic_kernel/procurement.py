from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from aoic_kernel.models import ProcurementRequest, ProcurementStatus


class Procurement:
    """Structured vendor procurement with dual review."""

    def __init__(self) -> None:
        self._requests: dict[str, ProcurementRequest] = {}

    def submit(
        self,
        vendor_name: str,
        purpose: str,
        amount: float,
        requested_by: str,
        recurring: bool = False,
        evidence: Optional[list[str]] = None,
        request_id: Optional[str] = None,
    ) -> ProcurementRequest:
        if amount <= 0:
            raise ValueError("amount must be positive")
        if not purpose:
            raise ValueError("purpose is required")
        request = ProcurementRequest(
            request_id=request_id or f"PROC-{uuid4().hex[:8].upper()}",
            vendor_name=vendor_name,
            purpose=purpose,
            amount=amount,
            recurring=recurring,
            requested_by=requested_by,
            evidence=evidence or [],
            created_at=datetime.now(timezone.utc),
        )
        self._requests[request.request_id] = request
        return request

    def get(self, request_id: str) -> ProcurementRequest:
        if request_id not in self._requests:
            raise KeyError(request_id)
        return self._requests[request_id]

    def vendor_review(self, request_id: str, reviewer: str, evidence: list[str]) -> ProcurementRequest:
        request = self.get(request_id)
        if request.status != ProcurementStatus.DRAFT:
            raise ValueError("vendor review requires DRAFT status")
        if not evidence:
            raise ValueError("vendor review requires evidence")
        request.status = ProcurementStatus.VENDOR_REVIEW
        request.evidence.extend([f"vendor:{reviewer}:{e}" for e in evidence])
        self._requests[request_id] = request
        return request

    def security_review(self, request_id: str, reviewer: str, evidence: list[str]) -> ProcurementRequest:
        request = self.get(request_id)
        if request.status != ProcurementStatus.VENDOR_REVIEW:
            raise ValueError("security review requires VENDOR_REVIEW status")
        if not evidence:
            raise ValueError("security review requires evidence")
        request.status = ProcurementStatus.SECURITY_REVIEW
        request.evidence.extend([f"security:{reviewer}:{e}" for e in evidence])
        self._requests[request_id] = request
        return request

    def approve(self, request_id: str, approver: str) -> ProcurementRequest:
        request = self.get(request_id)
        if request.status != ProcurementStatus.SECURITY_REVIEW:
            raise ValueError("approval requires SECURITY_REVIEW status")
        request.status = ProcurementStatus.APPROVED
        request.approved_by.append(approver)
        self._requests[request_id] = request
        return request

    def reject(self, request_id: str, reason: str) -> ProcurementRequest:
        request = self.get(request_id)
        if request.status in (ProcurementStatus.EXECUTED,):
            raise ValueError("cannot reject executed request")
        request.status = ProcurementStatus.REJECTED
        request.evidence.append(f"rejected: {reason}")
        self._requests[request_id] = request
        return request

    def execute(self, request_id: str) -> ProcurementRequest:
        request = self.get(request_id)
        if request.status != ProcurementStatus.APPROVED:
            raise ValueError("only APPROVED requests can be executed")
        request.status = ProcurementStatus.EXECUTED
        self._requests[request_id] = request
        return request
