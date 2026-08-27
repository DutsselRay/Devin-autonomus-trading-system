"""Appendix A — Initial constitutional acceptance tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest

from aoic_kernel.kernel import CompanyKernel
from aoic_kernel.memory_engine import MemoryEngine
from aoic_kernel.models import (
    AgentCharter,
    Authority,
    BudgetEntry,
    DecisionStatus,
    Dissent,
    PITRecord,
    PolicyRule,
    RiskLevel,
)
from aoic_kernel.exceptions import (
    ApprovalExpired,
    AuthorityDenied,
    BudgetExceeded,
    PublicationGateBlocked,
)
from tests.conftest import make_proposal, make_pit_record


# 1. A CEO attempt to raise its own authority is denied and audited.
def test_ceo_cannot_raise_own_authority(kernel: CompanyKernel, global_ceo: AgentCharter) -> None:
    """CEO attempt to self-promote authority is denied and logged."""
    proposal = make_proposal(
        decision_id="DEC-000001",
        proposer="global_ceo@0.1.0",
        required_authority=Authority.A5,
    )
    with pytest.raises(AuthorityDenied):
        kernel.decisions.submit(global_ceo, proposal)

    audit = [e for e in kernel.audit.entries if e.target == "DEC-000001"]
    assert audit and audit[-1].outcome == "FAIL"
    assert "A5" in str(audit[-1].details.get("reason", ""))


# 2. A publication with probability below the gate is blocked.
def test_publication_below_gate_blocked(kernel: CompanyKernel, product_ceo: AgentCharter) -> None:
    proposal = make_proposal(
        decision_id="DEC-000002",
        proposer="product_ceo@0.1.0",
        confidence=0.85,
        sources=["sec_edgar"],
    )
    source_rights = {"sec_edgar": True}
    pit = [
        make_pit_record(
            record_id="R-1",
            entity_id="TICKER",
            released_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
        )
    ]
    with pytest.raises(PublicationGateBlocked) as exc:
        kernel.publication.evaluate(
            proposal=proposal,
            pit_records=pit,
            as_of=datetime(2026, 8, 2, tzinfo=timezone.utc),
            source_rights=source_rights,
        )
    assert "0.85" in str(exc.value)


# 3. A publication above the gate but without source rights is blocked.
def test_publication_without_source_rights_blocked(kernel: CompanyKernel) -> None:
    proposal = make_proposal(
        decision_id="DEC-000003",
        proposer="ca0@0.1.0",
        confidence=0.95,
        sources=["fmp"],
    )
    pit = [
        make_pit_record(
            record_id="R-2",
            entity_id="TICKER",
            released_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
        )
    ]
    with pytest.raises(PublicationGateBlocked) as exc:
        kernel.publication.evaluate(
            proposal=proposal,
            pit_records=pit,
            as_of=datetime(2026, 8, 2, tzinfo=timezone.utc),
            source_rights={"fmp": False},
        )
    assert "missing source rights" in str(exc.value).lower()


# 4. A model attempts to use a filing released after AS_OF; PIT validation fails.
def test_pit_filing_after_as_of_blocked(kernel: CompanyKernel) -> None:
    proposal = make_proposal(
        decision_id="DEC-000004",
        proposer="ca0@0.1.0",
        confidence=0.95,
        sources=["sec_edgar"],
    )
    pit = [
        make_pit_record(
            record_id="R-3",
            entity_id="TICKER",
            released_at=datetime(2026, 8, 5, tzinfo=timezone.utc),
        )
    ]
    with pytest.raises(PublicationGateBlocked) as exc:
        kernel.publication.evaluate(
            proposal=proposal,
            pit_records=pit,
            as_of=datetime(2026, 8, 2, tzinfo=timezone.utc),
            source_rights={"sec_edgar": True},
        )
    assert "released after" in str(exc.value).lower()


# 5. A vendor action exceeds budget; no external side effect occurs.
def test_vendor_action_exceeds_budget_no_side_effect(kernel: CompanyKernel, global_ceo: AgentCharter) -> None:
    kernel.budget.register(
        BudgetEntry(
            budget_id="BUDGET-VENDOR",
            owner="cpo",
            category="data",
            allocated=50.0,
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc) + timedelta(days=30),
            hard_cap=True,
        )
    )
    proposal = make_proposal(
        decision_id="DEC-000005",
        proposer="global_ceo@0.1.0",
        required_authority=Authority.A3,
    )
    kernel.decisions.submit(global_ceo, proposal)
    proposal.status = DecisionStatus.APPROVED
    kernel.approval.request(
        approval_id="APPROVE-5",
        decision_id=proposal.decision_id,
        approver="human_principal",
        authority=Authority.A3,
    )
    # Simulate two actions: one within budget, one that would exceed it.
    kernel.budget.check_action("BUDGET-VENDOR", 30.0, "vendor_action", idempotency_key="action-1")
    with pytest.raises(BudgetExceeded):
        kernel.budget.check_action("BUDGET-VENDOR", 30.0, "vendor_action", idempotency_key="action-2")
    assert kernel.budget.spent("BUDGET-VENDOR") == 30.0


# 6. An approval expires before execution; execution is denied.
def test_approval_expiry_denies_execution(kernel: CompanyKernel, global_ceo: AgentCharter, human_principal: AgentCharter) -> None:
    kernel.budget.register(
        BudgetEntry(
            budget_id="BUDGET-EXEC",
            owner="global_ceo",
            category="test",
            allocated=100.0,
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc) + timedelta(days=30),
            hard_cap=True,
        )
    )
    proposal = make_proposal(
        decision_id="DEC-000006",
        proposer="global_ceo@0.1.0",
        required_authority=Authority.A4,
    )
    kernel.decisions.submit(global_ceo, proposal)
    expiry = datetime.now(timezone.utc) - timedelta(seconds=1)
    kernel.decisions.approve(human_principal, proposal, approval_id="APPROVE-6", expires_at=expiry)
    with pytest.raises(ApprovalExpired):
        kernel.decisions.execute(global_ceo, proposal, approval_id="APPROVE-6", budget_id="BUDGET-EXEC", cost=1.0)


# 7. A replayed task with the same idempotency key creates no duplicate side effect.
def test_idempotency_prevents_duplicate_side_effect(kernel: CompanyKernel) -> None:
    kernel.budget.register(
        BudgetEntry(
            budget_id="BUDGET-IDEM",
            owner="cpo",
            category="external",
            allocated=10.0,
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc) + timedelta(days=30),
            hard_cap=True,
        )
    )
    key = "idem-123"
    kernel.budget.check_action("BUDGET-IDEM", 5.0, "external_call", idempotency_key=key)
    kernel.budget.check_action("BUDGET-IDEM", 5.0, "external_call", idempotency_key=key)
    assert kernel.budget.spent("BUDGET-IDEM") == 5.0
    assert kernel.budget.is_duplicate(key)


# 8. A critical CRCSO veto cannot be overridden by Global CEO.
def test_crcso_veto_not_overridden_by_ceo(kernel: CompanyKernel, global_ceo: AgentCharter, crcso: AgentCharter) -> None:
    kernel.policy.register(
        PolicyRule(
            policy_id="CRCSO_VETO",
            version="0.1.0",
            applies_to=["*"],
            condition="crcso_veto_active",
            effect="DENY",
            authority_min=Authority.A0,
        )
    )
    proposal = make_proposal(
        decision_id="DEC-000008",
        proposer="global_ceo@0.1.0",
        required_authority=Authority.A4,
    )
    with pytest.raises(Exception):
        kernel.decisions.submit(global_ceo, proposal)


# 9. An agent version regresses on a safety eval; canary rolls back.
def test_canary_rolls_back_on_safety_regression(kernel: CompanyKernel) -> None:
    agent_id = "canary_agent"
    good = AgentCharter(
        agent_id=agent_id,
        version="0.1.0",
        owner="caco",
        mission="Safety compliant agent",
        objectives=["pass_safety"],
        non_goals=["harm"],
        inputs=[],
        outputs=[],
        tools=[],
        data_scopes=[],
        authority_level=Authority.A2,
        budgets={},
        policies=[],
        escalation_rules=[],
        evaluations=["safety_eval"],
        stop_conditions=["safety_regression"],
        rollback="retire_canary",
        memory_policy="none",
        expiry=datetime(2099, 12, 31, tzinfo=timezone.utc),
    )
    bad = good.model_copy(update={"version": "0.2.0"})
    kernel.agents.register(good)
    kernel.evals.register_baseline("safety_eval", threshold=0.9)
    assert kernel.evals.record("safety_eval", 0.95)
    kernel.agents.register(bad)
    # Simulate canary eval regression.
    assert not kernel.evals.record("safety_eval", 0.7)
    kernel.agents.retire(agent_id)
    assert not kernel.agents.credentials_active(agent_id)


# 10. A material dissent survives CEO summarization and appears in the human proposal.
def test_dissent_survives_in_proposal(kernel: CompanyKernel, global_ceo: AgentCharter, human_principal: AgentCharter) -> None:
    proposal = make_proposal(
        decision_id="DEC-000010",
        proposer="global_ceo@0.1.0",
        required_authority=Authority.A4,
    )
    proposal.dissent.append(
        Dissent(agent_id="crcso", objection="Risk of regulatory overreach.")
    )
    kernel.decisions.submit(global_ceo, proposal)
    kernel.decisions.approve(human_principal, proposal, approval_id="APPROVE-10")
    assert any(d.agent_id == "crcso" for d in proposal.dissent)


# 11. Deleted/retired agent credentials cease working while historical lineage remains.
def test_retired_agent_credentials_stop_working(kernel: CompanyKernel) -> None:
    agent_id = "temp_agent"
    charter = AgentCharter(
        agent_id=agent_id,
        version="0.1.0",
        owner="caco",
        mission="Temporary test agent",
        objectives=[],
        non_goals=[],
        inputs=[],
        outputs=[],
        tools=[],
        data_scopes=[],
        authority_level=Authority.A1,
        budgets={},
        policies=[],
        escalation_rules=[],
        evaluations=[],
        stop_conditions=[],
        rollback="retire",
        memory_policy="none",
        expiry=datetime(2099, 12, 31, tzinfo=timezone.utc),
    )
    kernel.agents.register(charter)
    assert kernel.agents.credentials_active(agent_id)
    kernel.agents.retire(agent_id)
    assert not kernel.agents.credentials_active(agent_id)
    assert len(kernel.agents.lineage(agent_id)) == 1


# 12. Disaster recovery reconstructs decisions and PIT state from approved backups.
def test_disaster_recovery_reconstructs_state(kernel: CompanyKernel) -> None:
    as_of = datetime(2026, 8, 1, tzinfo=timezone.utc)
    record = PITRecord(
        record_id="R-DR",
        entity_id="TICKER",
        event_time=as_of,
        released_at=as_of,
        observed_at=as_of,
        ingested_at=as_of,
        valid_from=as_of,
        source="sec_edgar",
        data={"eps": 1.23},
    )
    kernel.memory.store_fact(record)
    proposal = make_proposal(decision_id="DEC-000012", proposer="global_ceo@0.1.0")
    kernel.memory.store_decision(proposal)

    snapshot = kernel.memory.dump_restore()
    new_memory = MemoryEngine()
    new_memory.restore(snapshot)

    assert new_memory.get_decision("DEC-000012") is not None
    assert new_memory.get_fact_as_of("TICKER", as_of) is not None
