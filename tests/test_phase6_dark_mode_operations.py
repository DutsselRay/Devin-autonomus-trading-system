from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from aoic_kernel.kernel import CompanyKernel
from aoic_kernel.models import (
    Authority,
    CostEstimate,
    DecisionProposal,
    DecisionStatus,
    Evidence,
    Reversibility,
    RiskLevel,
    Severity,
    ValueEstimate,
)


def _proposal(decision_id: str, status: DecisionStatus = DecisionStatus.DRAFT) -> DecisionProposal:
    return DecisionProposal(
        decision_id=decision_id,
        proposer="agent-test@1.0.0",
        objective="test objective",
        problem="test problem",
        recommendation="buy",
        alternatives=["hold"],
        evidence=[Evidence(evidence_id="e1", as_of=datetime.now(timezone.utc), source="s1", hash="h1")],
        expected_value=ValueEstimate(low=-100.0, base=0.0, high=100.0),
        cost=CostEstimate(one_off=10.0, monthly=0.0),
        confidence=0.8,
        reversibility=Reversibility.MEDIUM,
        regulatory_risk=RiskLevel.LOW,
        strategic_impact="medium",
        urgency="medium",
        required_authority=Authority.A2,
        rollback_plan="reverse",
        status=status,
    )


def test_kernel_exposes_phase6_components():
    kernel = CompanyKernel()
    assert kernel.live_predictions is not None
    assert kernel.incidents is not None
    assert kernel.dashboard is not None
    assert kernel.audit_view is not None


def test_sealed_prediction_not_released_before_time():
    kernel = CompanyKernel()
    now = datetime.now(timezone.utc)
    prediction = kernel.live_predictions.record(
        entity_id="AAPL",
        feature_name="close",
        horizon=timedelta(days=1),
        predicted_value=150.0,
        probability=0.75,
        evidence=["backtest:uuid"],
        release_at=now + timedelta(hours=1),
    )
    assert kernel.live_predictions.get(prediction.prediction_id, as_of=now) is None


def test_sealed_prediction_released_at_time():
    kernel = CompanyKernel()
    now = datetime.now(timezone.utc)
    prediction = kernel.live_predictions.record(
        entity_id="AAPL",
        feature_name="close",
        horizon=timedelta(days=1),
        predicted_value=150.0,
        probability=0.75,
        evidence=["backtest:uuid"],
        release_at=now,
    )
    released = kernel.live_predictions.get(prediction.prediction_id, as_of=now)
    assert released is not None
    assert released.status == "RELEASED"


def test_prediction_resolve():
    kernel = CompanyKernel()
    now = datetime.now(timezone.utc)
    prediction = kernel.live_predictions.record(
        entity_id="AAPL",
        feature_name="close",
        horizon=timedelta(days=1),
        predicted_value=150.0,
        probability=0.75,
        evidence=["backtest:uuid"],
        release_at=now,
    )
    resolved = kernel.live_predictions.resolve(prediction.prediction_id, actual_value=155.0)
    assert resolved.actual_value == 155.0
    assert resolved.status == "RESOLVED"


def test_sealed_prediction_requires_evidence():
    kernel = CompanyKernel()
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError, match="evidence"):
        kernel.live_predictions.record(
            entity_id="AAPL",
            feature_name="close",
            horizon=timedelta(days=1),
            predicted_value=150.0,
            probability=0.75,
            evidence=[],
            release_at=now,
        )


def test_dashboard_snapshot_includes_released_predictions():
    kernel = CompanyKernel()
    now = datetime.now(timezone.utc)
    kernel.live_predictions.record(
        entity_id="AAPL",
        feature_name="close",
        horizon=timedelta(days=1),
        predicted_value=150.0,
        probability=0.75,
        evidence=["backtest:uuid"],
        release_at=now,
    )
    snapshot = kernel.dashboard.snapshot(as_of=now)
    assert len(snapshot.released_predictions) == 1


def test_dashboard_snapshot_includes_active_incidents():
    kernel = CompanyKernel()
    kernel.incidents.detect("API latency spike", "p99 > 2s", severity=Severity.HIGH)
    snapshot = kernel.dashboard.snapshot()
    assert len(snapshot.active_incidents) == 1


def test_incident_lifecycle():
    kernel = CompanyKernel()
    incident = kernel.incidents.detect("data drift", "feature distribution shifted", Severity.MEDIUM)
    kernel.incidents.classify(incident.incident_id, Severity.HIGH)
    kernel.incidents.contain(incident.incident_id)
    kernel.incidents.preserve_evidence(incident.incident_id, ["snapshot-1"])
    kernel.incidents.notify(incident.incident_id, "crcso")
    kernel.incidents.recover(incident.incident_id)
    kernel.incidents.verify(incident.incident_id)
    kernel.incidents.postmortem(incident.incident_id, "root cause: upstream schema change")
    kernel.incidents.remediate(incident.incident_id, "add schema drift detector")
    closed = kernel.incidents.close(incident.incident_id)
    assert closed.status == "CLOSED"


def test_incident_invalid_transition_blocked():
    kernel = CompanyKernel()
    incident = kernel.incidents.detect("anomaly", "anomaly", Severity.LOW)
    with pytest.raises(ValueError, match="Invalid transition"):
        kernel.incidents.close(incident.incident_id)


def test_incident_high_severity_active():
    kernel = CompanyKernel()
    incident = kernel.incidents.detect("security breach", "unauthorized token use", Severity.CRITICAL)
    kernel.incidents.classify(incident.incident_id, Severity.CRITICAL)
    active = kernel.incidents.list_active()
    assert any(i.severity == Severity.CRITICAL for i in active)


def test_audit_view_role_filtering():
    kernel = CompanyKernel()
    kernel.audit.append(
        entry_id="A-000001",
        event_type="PUBLICATION",
        actor="publication-agent",
        action="publish",
        target="research-1",
        outcome="PASS",
    )
    kernel.audit.append(
        entry_id="A-000002",
        event_type="DECISION_REJECTED",
        actor="agent-1",
        action="validate",
        target="DEC-000001",
        outcome="FAIL",
    )
    public = kernel.audit_view.query(role="public")
    assert len(public) == 1
    assert public[0].event_type == "PUBLICATION"
    auditor = kernel.audit_view.query(role="auditor")
    assert len(auditor) == 2


def test_audit_view_time_filter():
    kernel = CompanyKernel()
    t0 = datetime.now(timezone.utc)
    kernel.audit.append(
        entry_id="A-000003",
        event_type="PUBLICATION",
        actor="publication-agent",
        action="publish",
        target="research-1",
        outcome="PASS",
    )
    t1 = datetime.now(timezone.utc)
    results = kernel.audit_view.query(role="auditor", start=t0, end=t1)
    assert len(results) == 1


def test_dashboard_attention_score():
    kernel = CompanyKernel()
    proposals = [
        _proposal("DEC-000001"),
        _proposal("DEC-000002", status=DecisionStatus.VALIDATED),
    ]
    snapshot = kernel.dashboard.snapshot(proposals=proposals)
    assert snapshot.attention_score["count"] == 2
    assert snapshot.attention_score["max_score"] > 0
