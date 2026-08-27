from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from aoic_kernel.models import AuditFinding, RiskLevel


class EnterpriseAuditor:
    """External auditor engagement and finding registry."""

    def __init__(self) -> None:
        self._findings: dict[str, AuditFinding] = {}
        self._auditors: set[str] = set()

    def register_auditor(self, auditor: str) -> None:
        self._auditors.add(auditor)

    def submit_finding(
        self,
        scope: str,
        severity: RiskLevel,
        description: str,
        auditor: str,
        evidence: Optional[list[str]] = None,
    ) -> AuditFinding:
        if auditor not in self._auditors:
            raise ValueError("auditor must be registered")
        if not evidence:
            raise ValueError("finding requires evidence")
        finding = AuditFinding(
            finding_id=f"AUD-{uuid4().hex[:8].upper()}",
            scope=scope,
            severity=severity,
            description=description,
            evidence=evidence,
            auditor=auditor,
            reported_at=datetime.now(timezone.utc),
        )
        self._findings[finding.finding_id] = finding
        return finding

    def get(self, finding_id: str) -> AuditFinding:
        if finding_id not in self._findings:
            raise KeyError(finding_id)
        return self._findings[finding_id]

    def list_findings(self) -> list[AuditFinding]:
        return list(self._findings.values())

    def accept(self, finding_id: str) -> AuditFinding:
        finding = self.get(finding_id)
        finding.status = "ACCEPTED"
        self._findings[finding_id] = finding
        return finding

    def remediate(self, finding_id: str) -> AuditFinding:
        finding = self.get(finding_id)
        finding.status = "REMEDIATED"
        self._findings[finding_id] = finding
        return finding

    def dispute(self, finding_id: str, reason: str) -> AuditFinding:
        finding = self.get(finding_id)
        finding.status = "DISPUTED"
        finding.evidence.append(f"dispute: {reason}")
        self._findings[finding_id] = finding
        return finding
