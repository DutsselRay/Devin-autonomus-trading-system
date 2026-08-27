from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from aoic_kernel.kernel import CompanyKernel
from aoic_kernel.models import LaunchGateStatus


def test_kernel_exposes_phase7_components():
    kernel = CompanyKernel()
    assert kernel.commercial_readiness is not None
    assert kernel.public_track_record is not None
    assert kernel.billing_support is not None
    assert kernel.a5_launch is not None
    assert kernel.customer_web is not None


def test_commercial_readiness_not_ready_without_gates():
    kernel = CompanyKernel()
    assert not kernel.commercial_readiness.is_ready()
    status = kernel.commercial_readiness.readiness()
    assert status["missing"]


def test_commercial_readiness_ready_after_all_gates():
    kernel = CompanyKernel()
    for gate in kernel.commercial_readiness.required_gates:
        kernel.commercial_readiness.submit_gate(
            gate, LaunchGateStatus.PASSED, "crcso", evidence=["review-doc"]
        )
    assert kernel.commercial_readiness.is_ready()


def test_commercial_readiness_fails_if_any_gate_failed():
    kernel = CompanyKernel()
    for i, gate in enumerate(kernel.commercial_readiness.required_gates):
        status = LaunchGateStatus.FAILED if i == 0 else LaunchGateStatus.PASSED
        kernel.commercial_readiness.submit_gate(gate, status, "crcso", evidence=["review-doc"])
    assert not kernel.commercial_readiness.is_ready()


def test_public_track_record_only_includes_resolved_predictions():
    kernel = CompanyKernel()
    now = datetime.now(timezone.utc)
    p1 = kernel.live_predictions.record(
        entity_id="AAPL",
        feature_name="close",
        horizon=timedelta(days=1),
        predicted_value=150.0,
        probability=0.75,
        evidence=["backtest:uuid"],
        release_at=now,
    )
    kernel.live_predictions.resolve(p1.prediction_id, actual_value=155.0)
    p2 = kernel.live_predictions.record(
        entity_id="TSLA",
        feature_name="close",
        horizon=timedelta(days=1),
        predicted_value=200.0,
        probability=0.6,
        evidence=["backtest:uuid2"],
        release_at=now + timedelta(hours=1),
    )
    entries = kernel.public_track_record.build()
    assert len(entries) == 1
    assert entries[0].prediction_id == p1.prediction_id


def test_public_track_record_blocks_unsupported_claims():
    kernel = CompanyKernel()
    now = datetime.now(timezone.utc)
    p = kernel.live_predictions.record(
        entity_id="AAPL",
        feature_name="close",
        horizon=timedelta(days=1),
        predicted_value=150.0,
        probability=0.75,
        evidence=["backtest:uuid"],
        release_at=now,
    )
    kernel.live_predictions.resolve(p.prediction_id, actual_value=155.0)
    entries = kernel.public_track_record.build()
    assert entries[0].evidence
    assert "evidence" not in entries[0].claim.lower() or entries[0].evidence


def test_billing_support_registers_subscription():
    kernel = CompanyKernel()
    sub = kernel.billing_support.register_subscription("cust-1", "pro", 29.0)
    assert sub.customer_id == "cust-1"
    assert sub.plan == "pro"
    assert sub.status == "ACTIVE"


def test_billing_support_support_ticket_lifecycle():
    kernel = CompanyKernel()
    ticket = kernel.billing_support.create_ticket("cust-1", "cannot access report", "high")
    assert ticket.status == "OPEN"
    resolved = kernel.billing_support.resolve_ticket(ticket.ticket_id)
    assert resolved.status == "RESOLVED"
    assert resolved.resolved_at is not None


def test_a5_launch_requires_all_gates():
    kernel = CompanyKernel()
    decision = kernel.a5_launch.request_launch()
    with pytest.raises(ValueError, match="not all passed"):
        kernel.a5_launch.approve(decision.decision_id, "human-principal")


def test_a5_launch_approved_when_ready():
    kernel = CompanyKernel()
    for gate in kernel.commercial_readiness.required_gates:
        kernel.commercial_readiness.submit_gate(
            gate, LaunchGateStatus.PASSED, "crcso", evidence=["review-doc"]
        )
    decision = kernel.a5_launch.request_launch("track record verified")
    approved = kernel.a5_launch.approve(decision.decision_id, "human-principal")
    assert approved.status == "APPROVED"
    assert approved.approved_by == "human-principal"


def test_a5_launch_denied():
    kernel = CompanyKernel()
    decision = kernel.a5_launch.request_launch("too early")
    denied = kernel.a5_launch.deny(decision.decision_id, "human-principal", "insufficient evidence")
    assert denied.status == "DENIED"


def test_customer_web_requires_evidence_links():
    kernel = CompanyKernel()
    with pytest.raises(ValueError, match="evidence"):
        kernel.customer_web.publish_page("home", "Home", "Welcome", [])


def test_customer_web_publishes_page_with_evidence():
    kernel = CompanyKernel()
    page = kernel.customer_web.publish_page(
        "home",
        "Home",
        "Welcome to AOIC",
        ["https://audit/entry-1", "https://track/record-1"],
    )
    assert page["page_id"] == "home"
    assert len(page["evidence_links"]) == 2
    assert kernel.customer_web.get_page("home") == page


def test_public_track_record_excludes_sealed_predictions():
    kernel = CompanyKernel()
    now = datetime.now(timezone.utc)
    p = kernel.live_predictions.record(
        entity_id="AAPL",
        feature_name="close",
        horizon=timedelta(days=1),
        predicted_value=150.0,
        probability=0.75,
        evidence=["backtest:uuid"],
        release_at=now + timedelta(hours=2),
    )
    kernel.live_predictions.resolve(p.prediction_id, actual_value=155.0)
    entries = kernel.public_track_record.build(as_of=now)
    assert len(entries) == 0
