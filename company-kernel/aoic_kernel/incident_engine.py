from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from aoic_kernel.models import Incident, IncidentStatus, Severity


class IncidentEngine:
    """Incident tree: detect → classify → contain → preserve evidence → notify
    → recover → verify → postmortem → controlled remediation → close.
    """

    VALID_TRANSITIONS: dict[IncidentStatus, set[IncidentStatus]] = {
        IncidentStatus.DETECTED: {IncidentStatus.CLASSIFIED},
        IncidentStatus.CLASSIFIED: {IncidentStatus.CONTAINED},
        IncidentStatus.CONTAINED: {IncidentStatus.EVIDENCE_PRESERVED},
        IncidentStatus.EVIDENCE_PRESERVED: {IncidentStatus.NOTIFIED},
        IncidentStatus.NOTIFIED: {IncidentStatus.RECOVERING},
        IncidentStatus.RECOVERING: {IncidentStatus.VERIFIED},
        IncidentStatus.VERIFIED: {IncidentStatus.POSTMORTEM},
        IncidentStatus.POSTMORTEM: {IncidentStatus.REMEDIATED},
        IncidentStatus.REMEDIATED: {IncidentStatus.CLOSED},
        IncidentStatus.CLOSED: set(),
    }

    def __init__(self) -> None:
        self._incidents: dict[str, Incident] = {}

    def detect(
        self,
        title: str,
        description: str,
        severity: Severity | None = None,
        evidence: list[str] | None = None,
    ) -> Incident:
        incident = Incident(
            incident_id=f"INC-{uuid.uuid4().hex[:12]}",
            title=title,
            description=description,
            severity=severity or Severity.LOW,
            status=IncidentStatus.DETECTED,
            detected_at=datetime.now(timezone.utc),
            evidence=evidence or [],
        )
        self._incidents[incident.incident_id] = incident
        return incident

    def classify(self, incident_id: str, severity: Severity) -> Incident:
        return self._transition(incident_id, IncidentStatus.CLASSIFIED, severity=severity)

    def contain(self, incident_id: str) -> Incident:
        return self._transition(incident_id, IncidentStatus.CONTAINED, contained_at=datetime.now(timezone.utc))

    def preserve_evidence(self, incident_id: str, evidence: list[str]) -> Incident:
        incident = self._transition(incident_id, IncidentStatus.EVIDENCE_PRESERVED)
        incident.evidence.extend(evidence)
        return incident

    def notify(self, incident_id: str, authority: str) -> Incident:
        incident = self._transition(incident_id, IncidentStatus.NOTIFIED)
        incident.notifications.append(authority)
        return incident

    def recover(self, incident_id: str) -> Incident:
        return self._transition(incident_id, IncidentStatus.RECOVERING, recovered_at=datetime.now(timezone.utc))

    def verify(self, incident_id: str) -> Incident:
        return self._transition(incident_id, IncidentStatus.VERIFIED, verified_at=datetime.now(timezone.utc))

    def postmortem(self, incident_id: str, report: str) -> Incident:
        incident = self._transition(incident_id, IncidentStatus.POSTMORTEM, postmortem_at=datetime.now(timezone.utc))
        incident.postmortem_report = report
        return incident

    def remediate(self, incident_id: str, plan: str) -> Incident:
        incident = self._transition(incident_id, IncidentStatus.REMEDIATED, remediated_at=datetime.now(timezone.utc))
        incident.remediation_plan = plan
        return incident

    def close(self, incident_id: str) -> Incident:
        return self._transition(incident_id, IncidentStatus.CLOSED, closed_at=datetime.now(timezone.utc))

    def get(self, incident_id: str) -> Incident | None:
        return self._incidents.get(incident_id)

    def list_active(self) -> list[Incident]:
        return [i for i in self._incidents.values() if i.status != IncidentStatus.CLOSED]

    def list_by_severity(self, severity: Severity) -> list[Incident]:
        return [i for i in self._incidents.values() if i.severity == severity]

    def _transition(
        self,
        incident_id: str,
        target: IncidentStatus,
        **updates: Any,
    ) -> Incident:
        incident = self._incidents.get(incident_id)
        if incident is None:
            raise KeyError(f"Unknown incident {incident_id}")
        if target not in self.VALID_TRANSITIONS.get(incident.status, set()):
            raise ValueError(f"Invalid transition from {incident.status.value} to {target.value}")
        incident.status = target
        for key, value in updates.items():
            setattr(incident, key, value)
        return incident
