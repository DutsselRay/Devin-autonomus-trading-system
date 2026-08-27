from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aoic_kernel.audit_log import ImmutableAuditLog
from aoic_kernel.daily_briefing import HumanAttentionScore
from aoic_kernel.incident_engine import IncidentEngine
from aoic_kernel.live_prediction import LivePredictionRegistry
from aoic_kernel.models import AuditEntry, DashboardSnapshot, DecisionProposal, LivePrediction


class AuditView:
    """Read-only, role-filtered view over the immutable audit log."""

    def __init__(self, audit: ImmutableAuditLog) -> None:
        self.audit = audit

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for entry in self.audit.entries:
            counts[entry.event_type] = counts.get(entry.event_type, 0) + 1
        return counts

    def query(
        self,
        *,
        role: str = "public",
        agent_id: str | None = None,
        event_type: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[AuditEntry]:
        entries = self.audit.entries
        if role == "public":
            entries = [e for e in entries if e.event_type in {"PUBLICATION", "DECISION_APPROVED", "DECISION_EXECUTED"}]
        elif role == "agent" and agent_id:
            entries = [e for e in entries if e.actor == agent_id or e.target == agent_id or e.event_type in {"PUBLICATION"}]
        if event_type:
            entries = [e for e in entries if e.event_type == event_type]
        if start:
            entries = [e for e in entries if e.timestamp >= start]
        if end:
            entries = [e for e in entries if e.timestamp <= end]
        return entries


class InternalDashboard:
    """Read-only internal dashboard aggregating decisions, predictions, incidents and audit."""

    def __init__(
        self,
        audit: ImmutableAuditLog,
        attention: HumanAttentionScore,
        live_predictions: LivePredictionRegistry | None = None,
        incidents: IncidentEngine | None = None,
    ) -> None:
        self.audit = audit
        self.attention = attention
        self.live_predictions = live_predictions or LivePredictionRegistry()
        self.incidents = incidents or IncidentEngine()
        self.audit_view = AuditView(audit)

    def snapshot(
        self,
        *,
        proposals: list[DecisionProposal] | None = None,
        as_of: datetime | None = None,
    ) -> DashboardSnapshot:
        now = as_of or datetime.now(timezone.utc)
        proposals = proposals or []
        pending = [p for p in proposals if p.status in {"DRAFT", "VALIDATED", "CHALLENGED"}]
        released = self.live_predictions.list_released(as_of=now)
        active = self.incidents.list_active()
        if proposals:
            scores = [self.attention.score(p) for p in proposals]
            attention_score = {"count": len(proposals), "max_score": max(scores), "scores": scores}
        else:
            attention_score = {"count": 0, "max_score": 0.0, "scores": []}
        return DashboardSnapshot(
            snapshot_at=now,
            pending_decisions=pending,
            released_predictions=released,
            active_incidents=active,
            attention_score=attention_score,
            audit_summary=self.audit_view.summary(),
        )

    def released_predictions(self, as_of: datetime | None = None) -> list[LivePrediction]:
        return self.live_predictions.list_released(as_of=as_of)

    def active_incidents(self) -> list[Any]:
        return self.incidents.list_active()
