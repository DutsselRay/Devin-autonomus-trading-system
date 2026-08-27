from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from aoic_kernel.models import B2BProductGate, B2BProductGateStatus


class B2BGate:
    """Gate that blocks professional/B2B products until V1 proof is evidenced."""

    def __init__(self) -> None:
        self._gates: dict[str, B2BProductGate] = {}

    def register(self, product_id: str, name: str) -> B2BProductGate:
        gate = B2BProductGate(product_id=product_id, name=name)
        self._gates[product_id] = gate
        return gate

    def get(self, product_id: str) -> B2BProductGate:
        if product_id not in self._gates:
            raise KeyError(product_id)
        return self._gates[product_id]

    def submit_v1_proof(self, product_id: str, evidence: list[str]) -> B2BProductGate:
        gate = self.get(product_id)
        if gate.status != B2BProductGateStatus.BLOCKED:
            raise ValueError("V1 proof can only be submitted when gate is BLOCKED")
        if not evidence:
            raise ValueError("V1 proof requires evidence")
        gate.v1_proof_evidence.extend(evidence)
        gate.status = B2BProductGateStatus.V1_PROOF
        self._gates[product_id] = gate
        return gate

    def approve(
        self,
        product_id: str,
        approver: str,
        evidence: Optional[list[str]] = None,
    ) -> B2BProductGate:
        gate = self.get(product_id)
        if gate.status != B2BProductGateStatus.V1_PROOF:
            raise ValueError("product must have V1_PROOF status before approval")
        gate.status = B2BProductGateStatus.APPROVED
        gate.approved_by = approver
        gate.approved_at = datetime.now(timezone.utc)
        if evidence:
            gate.v1_proof_evidence.extend(evidence)
        self._gates[product_id] = gate
        return gate
