from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from aoic_kernel.kernel import CompanyKernel
from aoic_kernel.models import AgentCharter, Authority, CapabilityProposal, SkillContract

FUTURE = datetime.now(timezone.utc) + timedelta(days=365)


def _charter(agent_id: str, version: str) -> AgentCharter:
    return AgentCharter(
        agent_id=agent_id,
        version=version,
        owner="caco",
        mission=f"Mission for {agent_id} v{version}",
        objectives=["execute"],
        non_goals=["self-modify"],
        inputs=["data"],
        outputs=["decisions"],
        tools=["screen"],
        data_scopes=["market"],
        authority_level=Authority.A2,
        budgets={},
        policies=["policy-1"],
        escalation_rules=["escalate"],
        evaluations=["eval"],
        stop_conditions=["stop"],
        rollback="rollback",
        memory_policy="immutable",
        expiry=FUTURE,
        status="ACTIVE",
    )


def _skill(skill_id: str, version: str) -> SkillContract:
    return SkillContract(
        skill_id=skill_id,
        version=version,
        purpose=f"Skill {skill_id} v{version}",
        preconditions=[],
        input_schema="string",
        output_schema="string",
        side_effects=[],
        required_permissions=[],
        cost_model="flat",
        latency_slo="1s",
        failure_modes=[],
        evidence_requirements=[],
        tests=["unit"],
        security_classification="internal",
        idempotency="yes",
        status="APPROVED",
    )


def _proposal(agent_id: str, version: str, proposer: str = "caco") -> CapabilityProposal:
    return CapabilityProposal(
        proposal_id=f"cp-{agent_id}-{version}",
        agent_id=agent_id,
        agent_version=version,
        proposer=proposer,
        capability_gap="improve forecasting",
        expected_value={"accuracy": 0.1},
    )


def test_kernel_exposes_caco_shadow_and_canary():
    kernel = CompanyKernel()
    assert kernel.agent_lifecycle is not None
    assert kernel.shadow is not None
    assert kernel.canary is not None


def test_capability_proposal_self_modification_guard():
    kernel = CompanyKernel()
    proposal = _proposal("analyst", "1.1.0", proposer="analyst")
    with pytest.raises(ValueError, match="itself"):
        kernel.agent_lifecycle.propose(proposal)


def test_source_review_fail_blocks_lifecycle():
    kernel = CompanyKernel()
    proposal = _proposal("analyst", "1.1.0")
    kernel.agent_lifecycle.propose(proposal)
    result = kernel.agent_lifecycle.review_source_license(
        proposal.proposal_id,
        source_reviewed=False,
        license_approved=True,
        security_reviewed=True,
    )
    assert result.status == "ROLLED_BACK"


def test_register_charter_after_source_review():
    kernel = CompanyKernel()
    proposal = _proposal("analyst", "1.1.0")
    lifecycle = kernel.agent_lifecycle
    lifecycle.propose(proposal)
    lifecycle.review_source_license(
        proposal.proposal_id,
        source_reviewed=True,
        license_approved=True,
        security_reviewed=True,
    )
    charter = _charter("analyst", "1.1.0")
    skill = _skill("analysis", "1.1.0")
    lifecycle.register_charter(proposal.proposal_id, charter, [skill])
    assert proposal.charter_contract == charter


def test_benchmark_requires_adversarial_pass():
    kernel = CompanyKernel()
    proposal = _proposal("analyst", "1.1.0")
    lifecycle = kernel.agent_lifecycle
    lifecycle.propose(proposal)
    lifecycle.review_source_license(proposal.proposal_id, source_reviewed=True, license_approved=True, security_reviewed=True)
    lifecycle.run_benchmark(
        proposal.proposal_id,
        runner=lambda a, v: 1.0,
        adversarial_runner=lambda a, v: False,
        threshold=0.0,
    )
    assert proposal.benchmark_passed
    assert not proposal.adversarial_tests_passed
    assert proposal.status == "ROLLED_BACK"


def test_shadow_challenger_wins_promotes_to_shadow():
    kernel = CompanyKernel()
    incumbent = _charter("analyst", "1.0.0")
    kernel.agents.register(incumbent)
    proposal = _proposal("analyst", "1.1.0")
    lifecycle = kernel.agent_lifecycle
    lifecycle.propose(proposal)
    lifecycle.review_source_license(proposal.proposal_id, source_reviewed=True, license_approved=True, security_reviewed=True)
    lifecycle.run_benchmark(
        proposal.proposal_id,
        runner=lambda a, v: 1.0,
        adversarial_runner=lambda a, v: True,
        threshold=0.0,
    )
    challenge = lifecycle.run_shadow(
        proposal.proposal_id,
        incumbent_id="analyst",
        benchmark_id="fixed-eval",
        metric="score",
        runner=lambda a, v: 1.5 if v == "1.1.0" else 1.0,
        baseline_runner=lambda: 0.1,
    )
    assert challenge.winner == "challenger"
    assert proposal.status == "SHADOW"


def test_shadow_challenger_loses_rolls_back():
    kernel = CompanyKernel()
    incumbent = _charter("analyst", "1.0.0")
    kernel.agents.register(incumbent)
    proposal = _proposal("analyst", "1.1.0")
    lifecycle = kernel.agent_lifecycle
    lifecycle.propose(proposal)
    lifecycle.review_source_license(proposal.proposal_id, source_reviewed=True, license_approved=True, security_reviewed=True)
    lifecycle.run_benchmark(
        proposal.proposal_id,
        runner=lambda a, v: 1.0,
        adversarial_runner=lambda a, v: True,
        threshold=0.0,
    )
    lifecycle.run_shadow(
        proposal.proposal_id,
        incumbent_id="analyst",
        benchmark_id="fixed-eval",
        metric="score",
        runner=lambda a, v: 0.5 if v == "1.1.0" else 1.0,
        baseline_runner=lambda: 0.1,
    )
    assert proposal.status == "ROLLED_BACK"


def test_canary_limited_scope_and_fails_rollback():
    kernel = CompanyKernel()
    incumbent = _charter("analyst", "1.0.0")
    kernel.agents.register(incumbent)
    proposal = _proposal("analyst", "1.1.0")
    lifecycle = kernel.agent_lifecycle
    lifecycle.propose(proposal)
    lifecycle.review_source_license(proposal.proposal_id, source_reviewed=True, license_approved=True, security_reviewed=True)
    lifecycle.run_benchmark(
        proposal.proposal_id,
        runner=lambda a, v: 1.0,
        adversarial_runner=lambda a, v: True,
        threshold=0.0,
    )
    lifecycle.run_shadow(
        proposal.proposal_id,
        incumbent_id="analyst",
        benchmark_id="fixed-eval",
        metric="score",
        runner=lambda a, v: 1.5 if v == "1.1.0" else 1.0,
        baseline_runner=lambda: 0.1,
    )
    run = lifecycle.run_canary(
        proposal.proposal_id,
        previous_version="1.0.0",
        scope="limited-5pct",
        acceptance_criteria={"accuracy": 0.9},
        metrics={"accuracy": 0.7},
    )
    assert run.status == "FAILED"
    assert proposal.status == "ROLLED_BACK"
    assert len(kernel.canary.list_rollbacks(proposal.agent_id)) == 1


def test_canary_passes_then_promote():
    kernel = CompanyKernel()
    incumbent = _charter("analyst", "1.0.0")
    kernel.agents.register(incumbent)
    proposal = _proposal("analyst", "1.1.0")
    lifecycle = kernel.agent_lifecycle
    charter = _charter("analyst", "1.1.0")
    lifecycle.propose(proposal)
    lifecycle.review_source_license(proposal.proposal_id, source_reviewed=True, license_approved=True, security_reviewed=True)
    lifecycle.register_charter(proposal.proposal_id, charter, [_skill("analysis", "1.1.0")])
    lifecycle.run_benchmark(
        proposal.proposal_id,
        runner=lambda a, v: 1.0,
        adversarial_runner=lambda a, v: True,
        threshold=0.0,
    )
    lifecycle.run_shadow(
        proposal.proposal_id,
        incumbent_id="analyst",
        benchmark_id="fixed-eval",
        metric="score",
        runner=lambda a, v: 1.5 if v == "1.1.0" else 1.0,
        baseline_runner=lambda: 0.1,
    )
    run = lifecycle.run_canary(
        proposal.proposal_id,
        previous_version="1.0.0",
        scope="limited-5pct",
        acceptance_criteria={"accuracy": 0.9},
        metrics={"accuracy": 0.95},
    )
    assert run.status == "PASSED"
    decision = lifecycle.promote(proposal.proposal_id, approvers=["crcso", "cfo"])
    assert decision.status == "APPROVED"
    assert kernel.agents.get("analyst").version == "1.1.0"


def test_promotion_cannot_be_self_approved():
    kernel = CompanyKernel()
    incumbent = _charter("analyst", "1.0.0")
    kernel.agents.register(incumbent)
    proposal = _proposal("analyst", "1.1.0")
    lifecycle = kernel.agent_lifecycle
    charter = _charter("analyst", "1.1.0")
    lifecycle.propose(proposal)
    lifecycle.review_source_license(proposal.proposal_id, source_reviewed=True, license_approved=True, security_reviewed=True)
    lifecycle.register_charter(proposal.proposal_id, charter, [_skill("analysis", "1.1.0")])
    lifecycle.run_benchmark(
        proposal.proposal_id,
        runner=lambda a, v: 1.0,
        adversarial_runner=lambda a, v: True,
        threshold=0.0,
    )
    lifecycle.run_shadow(
        proposal.proposal_id,
        incumbent_id="analyst",
        benchmark_id="fixed-eval",
        metric="score",
        runner=lambda a, v: 1.5 if v == "1.1.0" else 1.0,
        baseline_runner=lambda: 0.1,
    )
    run = lifecycle.run_canary(
        proposal.proposal_id,
        previous_version="1.0.0",
        scope="limited-5pct",
        acceptance_criteria={"accuracy": 0.0},
        metrics={"accuracy": 1.0},
    )
    assert run.status == "PASSED"
    with pytest.raises(ValueError, match="own promotion"):
        lifecycle.promote(proposal.proposal_id, approvers=["analyst"])


def test_rollback_restores_previous_version():
    kernel = CompanyKernel()
    incumbent = _charter("analyst", "1.0.0")
    kernel.agents.register(incumbent)
    proposal = _proposal("analyst", "1.1.0")
    lifecycle = kernel.agent_lifecycle
    charter = _charter("analyst", "1.1.0")
    lifecycle.propose(proposal)
    lifecycle.review_source_license(proposal.proposal_id, source_reviewed=True, license_approved=True, security_reviewed=True)
    lifecycle.register_charter(proposal.proposal_id, charter, [_skill("analysis", "1.1.0")])
    lifecycle.run_benchmark(
        proposal.proposal_id,
        runner=lambda a, v: 1.0,
        adversarial_runner=lambda a, v: True,
        threshold=0.0,
    )
    lifecycle.run_shadow(
        proposal.proposal_id,
        incumbent_id="analyst",
        benchmark_id="fixed-eval",
        metric="score",
        runner=lambda a, v: 1.5 if v == "1.1.0" else 1.0,
        baseline_runner=lambda: 0.1,
    )
    run = lifecycle.run_canary(
        proposal.proposal_id,
        previous_version="1.0.0",
        scope="limited-5pct",
        acceptance_criteria={"accuracy": 0.9},
        metrics={"accuracy": 0.95},
    )
    assert run.status == "PASSED"
    lifecycle.promote(proposal.proposal_id, approvers=["crcso", "cfo"])
    assert kernel.agents.get("analyst").version == "1.1.0"

    record = lifecycle.rollback(proposal.proposal_id, previous_version="1.0.0", reason="regression")
    assert record.previous_version == "1.0.0"
    assert record.new_version == "1.1.0"
    assert kernel.agents.get("analyst").version == "1.0.0"


def test_promotion_registers_new_version_and_keeps_old_in_history():
    kernel = CompanyKernel()
    incumbent = _charter("analyst", "1.0.0")
    kernel.agents.register(incumbent)
    proposal = _proposal("analyst", "1.1.0")
    lifecycle = kernel.agent_lifecycle
    charter = _charter("analyst", "1.1.0")
    lifecycle.propose(proposal)
    lifecycle.review_source_license(proposal.proposal_id, source_reviewed=True, license_approved=True, security_reviewed=True)
    lifecycle.register_charter(proposal.proposal_id, charter, [_skill("analysis", "1.1.0")])
    lifecycle.run_benchmark(
        proposal.proposal_id,
        runner=lambda a, v: 1.0,
        adversarial_runner=lambda a, v: True,
        threshold=0.0,
    )
    lifecycle.run_shadow(
        proposal.proposal_id,
        incumbent_id="analyst",
        benchmark_id="fixed-eval",
        metric="score",
        runner=lambda a, v: 1.5 if v == "1.1.0" else 1.0,
        baseline_runner=lambda: 0.1,
    )
    run = lifecycle.run_canary(
        proposal.proposal_id,
        previous_version="1.0.0",
        scope="limited-5pct",
        acceptance_criteria={"accuracy": 0.9},
        metrics={"accuracy": 0.95},
    )
    assert run.status == "PASSED"
    lifecycle.promote(proposal.proposal_id, approvers=["crcso", "cfo"])
    history = kernel.agents.lineage("analyst")
    versions = {c.version for c in history}
    assert versions == {"1.0.0", "1.1.0"}


def test_lifecycle_failure_recorded():
    kernel = CompanyKernel()
    proposal = _proposal("analyst", "1.1.0")
    lifecycle = kernel.agent_lifecycle
    lifecycle.propose(proposal)
    lifecycle.review_source_license(
        proposal.proposal_id,
        source_reviewed=False,
        license_approved=True,
        security_reviewed=True,
    )
    assert lifecycle.get_proposal(proposal.proposal_id).status == "ROLLED_BACK"
