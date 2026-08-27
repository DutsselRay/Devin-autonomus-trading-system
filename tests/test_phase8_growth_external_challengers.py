from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from aoic_kernel.kernel import CompanyKernel
from aoic_kernel.models import RiskLevel


def test_kernel_exposes_phase8_components():
    kernel = CompanyKernel()
    assert kernel.cmo_growth is not None
    assert kernel.procurement is not None
    assert kernel.enterprise_audit is not None
    assert kernel.red_team is not None
    assert kernel.b2b_gate is not None


def test_cmo_growth_campaign_lifecycle():
    kernel = CompanyKernel()
    start = datetime.now(timezone.utc)
    campaign = kernel.cmo_growth.create(
        "Q4 outreach", "email", "institutional investors", 5000.0, start
    )
    assert campaign.status == "DRAFT"
    kernel.cmo_growth.review(campaign.campaign_id, ["audience-ok"])
    kernel.cmo_growth.start(campaign.campaign_id)
    assert kernel.cmo_growth.get(campaign.campaign_id).status == "RUNNING"
    kernel.cmo_growth.pause(campaign.campaign_id, "budget check")
    assert kernel.cmo_growth.get(campaign.campaign_id).status == "PAUSED"
    kernel.cmo_growth.complete(campaign.campaign_id)
    assert kernel.cmo_growth.get(campaign.campaign_id).status == "COMPLETED"


def test_cmo_growth_requires_evidence_for_review():
    kernel = CompanyKernel()
    start = datetime.now(timezone.utc)
    campaign = kernel.cmo_growth.create("x", "x", "x", 0.0, start)
    with pytest.raises(ValueError, match="evidence"):
        kernel.cmo_growth.review(campaign.campaign_id, [])


def test_cmo_growth_lead_tracking():
    kernel = CompanyKernel()
    start = datetime.now(timezone.utc)
    campaign = kernel.cmo_growth.create("leads", "web", "retail", 1000.0, start)
    kernel.cmo_growth.review(campaign.campaign_id, ["audience-ok"])
    kernel.cmo_growth.start(campaign.campaign_id)
    updated = kernel.cmo_growth.add_lead(campaign.campaign_id, "lead-1")
    assert "lead-1" in updated.leads


def test_procurement_dual_review_lifecycle():
    kernel = CompanyKernel()
    req = kernel.procurement.submit("Vendor A", "cloud hosting", 500.0, "engineer-1")
    assert req.status == "DRAFT"
    kernel.procurement.vendor_review(req.request_id, "buyer", ["quote"])
    kernel.procurement.security_review(req.request_id, "infosec", ["compliance"])
    kernel.procurement.approve(req.request_id, "cfo")
    executed = kernel.procurement.execute(req.request_id)
    assert executed.status == "EXECUTED"


def test_procurement_cannot_execute_before_approval():
    kernel = CompanyKernel()
    req = kernel.procurement.submit("Vendor B", "saas", 100.0, "engineer-2")
    with pytest.raises(ValueError, match="APPROVED"):
        kernel.procurement.execute(req.request_id)


def test_procurement_reject():
    kernel = CompanyKernel()
    req = kernel.procurement.submit("Vendor C", "consulting", 10000.0, "pm-1")
    rejected = kernel.procurement.reject(req.request_id, "budget freeze")
    assert rejected.status == "REJECTED"


def test_enterprise_auditor_requires_registration():
    kernel = CompanyKernel()
    with pytest.raises(ValueError, match="registered"):
        kernel.enterprise_audit.submit_finding(
            "payments", RiskLevel.HIGH, "missing logs", "unregistered-auditor", evidence=["ev1"]
        )


def test_enterprise_auditor_finding_lifecycle():
    kernel = CompanyKernel()
    kernel.enterprise_audit.register_auditor("external-1")
    finding = kernel.enterprise_audit.submit_finding(
        "access control", RiskLevel.HIGH, "stale keys", "external-1", evidence=["key-list"]
    )
    kernel.enterprise_audit.accept(finding.finding_id)
    assert kernel.enterprise_audit.get(finding.finding_id).status == "ACCEPTED"
    kernel.enterprise_audit.remediate(finding.finding_id)
    assert kernel.enterprise_audit.get(finding.finding_id).status == "REMEDIATED"


def test_enterprise_auditor_dispute():
    kernel = CompanyKernel()
    kernel.enterprise_audit.register_auditor("external-2")
    finding = kernel.enterprise_audit.submit_finding(
        "data", RiskLevel.MEDIUM, "sample issue", "external-2", evidence=["doc"]
    )
    kernel.enterprise_audit.dispute(finding.finding_id, "scope mismatch")
    assert kernel.enterprise_audit.get(finding.finding_id).status == "DISPUTED"


def test_red_team_exercise_lifecycle():
    kernel = CompanyKernel()
    exercise = kernel.red_team.plan("prediction-api", "try prompt injection", ["red-1", "red-2"])
    assert exercise.status == "PLANNED"
    kernel.red_team.start(exercise.exercise_id)
    completed = kernel.red_team.complete(exercise.exercise_id, ["finding-1", "finding-2"])
    assert completed.status == "COMPLETED"
    assert len(completed.findings) == 2


def test_red_team_cannot_complete_without_start():
    kernel = CompanyKernel()
    exercise = kernel.red_team.plan("api", "test", ["red-1"])
    with pytest.raises(ValueError, match="RUNNING"):
        kernel.red_team.complete(exercise.exercise_id, ["f"])


def test_b2b_gate_blocks_without_v1_proof():
    kernel = CompanyKernel()
    kernel.b2b_gate.register("pro-dashboard", "Professional Dashboard")
    with pytest.raises(ValueError, match="V1_PROOF"):
        kernel.b2b_gate.approve("pro-dashboard", "product-lead")


def test_b2b_gate_requires_evidence_for_proof():
    kernel = CompanyKernel()
    kernel.b2b_gate.register("pro-dashboard", "Professional Dashboard")
    with pytest.raises(ValueError, match="evidence"):
        kernel.b2b_gate.submit_v1_proof("pro-dashboard", [])


def test_b2b_gate_approves_after_v1_proof():
    kernel = CompanyKernel()
    gate = kernel.b2b_gate.register("api-tier", "API Tier")
    kernel.b2b_gate.submit_v1_proof("api-tier", ["public-track-record-ok"])
    approved = kernel.b2b_gate.approve("api-tier", "cso")
    assert approved.status == "APPROVED"
    assert approved.approved_by == "cso"
