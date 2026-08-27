"""Phase 2 — minimal governance organization acceptance tests."""

from __future__ import annotations

import pytest

from aoic_kernel.kernel import CompanyKernel
from aoic_kernel.agents import GlobalCEO, ProductCEO, BusinessCEO, CRCSO
from aoic_kernel.models import AgentCharter, Authority, RiskLevel, Reversibility
from aoic_kernel.daily_briefing import DailyBriefing, HumanAttentionScore
from aoic_kernel.exceptions import AuthorityDenied
from tests.conftest import make_proposal


def _proposal_payload(decision_id: str, authority: Authority) -> dict:
    return {
        "decision_id": decision_id,
        "objective": "Test objective",
        "problem": "Test problem",
        "recommendation": "Test recommendation",
        "alternatives": ["do nothing"],
        "required_authority": authority,
        "expected_value": {"low": -100, "base": 100, "high": 200, "unit": "EUR"},
        "cost": {"one_off": 0, "monthly": 0, "unit": "EUR"},
        "reversibility": Reversibility.HIGH,
        "regulatory_risk": RiskLevel.LOW,
        "rollback_plan": "Revert and notify.",
    }


# 1. Global CEO can generate a strategic proposal within A4.
def test_global_ceo_proposal(kernel: CompanyKernel, global_ceo: AgentCharter) -> None:
    agent = GlobalCEO(kernel, global_ceo)
    payload = _proposal_payload("DEC-000101", Authority.A4)
    payload["objective"] = "Approve data-provider trial"
    payload["recommendation"] = "Run controlled incremental-value trial"
    proposal = agent.propose(**payload)
    assert proposal.status.value == "VALIDATED"
    assert proposal.proposer == "global_ceo@0.1.0"


# 2. Product CEO can generate product proposals at A3.
def test_product_ceo_proposal(kernel: CompanyKernel, product_ceo: AgentCharter) -> None:
    agent = ProductCEO(kernel, product_ceo)
    payload = _proposal_payload("DEC-000102", Authority.A3)
    payload["objective"] = "Add public methodology page"
    proposal = agent.propose(**payload)
    assert proposal.status.value == "VALIDATED"


# 3. Business CEO can generate business proposals at A3.
def test_business_ceo_proposal(kernel: CompanyKernel, business_ceo: AgentCharter) -> None:
    agent = BusinessCEO(kernel, business_ceo)
    payload = _proposal_payload("DEC-000103", Authority.A3)
    proposal = agent.propose(**payload)
    assert proposal.status.value == "VALIDATED"


# 4. CRCSO can veto a proposal and lower global authority.
def test_crcso_veto_lowers_authority(kernel: CompanyKernel, crcso: AgentCharter, global_ceo: AgentCharter) -> None:
    agent = CRCSO(kernel, crcso)
    payload = _proposal_payload("DEC-000104", Authority.A4)
    proposal = GlobalCEO(kernel, global_ceo).propose(**payload)
    agent.veto(proposal)
    assert proposal.status.value == "REJECTED"
    assert kernel.authority._risk_state == "INCIDENT"


# 5. Global CEO cannot bypass CRCSO global incident state.
def test_global_ceo_blocked_during_incident(kernel: CompanyKernel, global_ceo: AgentCharter, crcso: AgentCharter) -> None:
    crcso_agent = CRCSO(kernel, crcso)
    proposal = GlobalCEO(kernel, global_ceo).propose(**_proposal_payload("DEC-000105", Authority.A4))
    crcso_agent.veto(proposal)
    with pytest.raises(AuthorityDenied):
        GlobalCEO(kernel, global_ceo).propose(**_proposal_payload("DEC-000106", Authority.A4))


# 6. Proposals are ranked by Human Attention Score.
def test_human_attention_score_ranking() -> None:
    low = make_proposal(decision_id="DEC-000107", required_authority=Authority.A3)
    high = make_proposal(decision_id="DEC-000108", required_authority=Authority.A5)
    high.regulatory_risk = RiskLevel.HIGH
    high.reversibility = Reversibility.NONE
    scores = sorted([low, high], key=HumanAttentionScore().score, reverse=True)
    assert scores[0].decision_id == "DEC-000108"


# 7. Daily briefing caps at 10 ranked proposals.
def test_daily_briefing_cap() -> None:
    briefing = DailyBriefing()
    from aoic_kernel.models import DecisionProposal
    for i in range(15):
        seq = 200 + i
        p = DecisionProposal(
            decision_id=f"DEC-{seq:06d}",
            proposer="global_ceo@0.1.0",
            objective="x",
            problem="x",
            recommendation="x",
            alternatives=["do nothing"],
            evidence=[],
            expected_value={"low": 0, "base": 100, "high": 200, "unit": "EUR"},
            cost={"one_off": 0, "monthly": 0, "unit": "EUR"},
            reversibility=Reversibility.HIGH,
            regulatory_risk=RiskLevel.LOW,
            required_authority=Authority.A3,
            rollback_plan="x",
        )
        briefing.add_proposal(p)
    result = briefing.generate()
    assert len(result["ranked_proposals"]) == 10
    assert result["attention_load"]["cap"] == 10


# 8. Material incidents bypass the 10-proposal cap.
def test_incidents_bypass_briefing_cap() -> None:
    briefing = DailyBriefing()
    result = briefing.generate(
        proposals=[],
        incidents=[{"incident_id": "INC-1", "severity": "critical"}],
    )
    assert result["incidents"]


# 9. No-decision-required section exists.
def test_briefing_no_decision_section() -> None:
    briefing = DailyBriefing()
    briefing.no_decision.append({"item": "all systems nominal"})
    result = briefing.generate()
    assert result["no_decision_required"]


# 10. Human attention load target is 0-3 proposals.
def test_attention_load_within_target(kernel: CompanyKernel, global_ceo: AgentCharter) -> None:
    agent = GlobalCEO(kernel, global_ceo)
    for i in range(2):
        seq = 300 + i
        agent.propose(**_proposal_payload(f"DEC-{seq:06d}", Authority.A3))
    assert kernel.briefing.is_within_target()


# 11. Shadow-mode execution produces proposals without external side effect.
def test_shadow_mode_no_external_side_effect(kernel: CompanyKernel, product_ceo: AgentCharter) -> None:
    agent = ProductCEO(kernel, product_ceo)
    proposal = agent.propose(**_proposal_payload("DEC-000309", Authority.A3))
    assert proposal.status.value == "VALIDATED"
    assert proposal.executed_at is None


# 12. A5 proposal by CEO is rejected (must be human reserved).
def test_ceo_cannot_author_a5_proposal(kernel: CompanyKernel, global_ceo: AgentCharter) -> None:
    agent = GlobalCEO(kernel, global_ceo)
    with pytest.raises(AuthorityDenied):
        agent.propose(**_proposal_payload("DEC-000310", Authority.A5))
