from __future__ import annotations

import inspect
import uuid
from typing import Any, Callable

from aoic_kernel.agent_registry import AgentRegistry
from aoic_kernel.canary_rollback import CanaryRollback
from aoic_kernel.models import (
    AgentCharter,
    CapabilityProposal,
    PromotionDecision,
    ShadowChallenge,
)
from aoic_kernel.shadow_challenger import ShadowChallenger
from aoic_kernel.skill_registry import SkillRegistry


class AgentLifecycle:
    """CACO capability lifecycle: proposal, review, benchmark, shadow, canary, promotion, rollback."""

    def __init__(
        self,
        agent_registry: AgentRegistry,
        skill_registry: SkillRegistry,
        shadow_challenger: ShadowChallenger,
        canary_rollback: CanaryRollback,
    ) -> None:
        self.agents = agent_registry
        self.skills = skill_registry
        self.shadow = shadow_challenger
        self.canary = canary_rollback
        self._proposals: dict[str, CapabilityProposal] = {}
        self._promotions: dict[str, PromotionDecision] = {}

    def propose(self, proposal: CapabilityProposal) -> CapabilityProposal:
        if proposal.proposer == proposal.agent_id:
            raise ValueError("an agent may not propose changes to itself")
        self._proposals[proposal.proposal_id] = proposal
        return proposal

    def review_source_license(
        self,
        proposal_id: str,
        *,
        source_reviewed: bool,
        license_approved: bool,
        security_reviewed: bool,
    ) -> CapabilityProposal:
        proposal = self._get_proposal(proposal_id)
        proposal.source_reviewed = source_reviewed
        proposal.license_approved = license_approved
        proposal.security_reviewed = security_reviewed
        if source_reviewed and license_approved and security_reviewed:
            proposal.status = "REVIEWED"
        else:
            proposal.status = "ROLLED_BACK"
        return proposal

    def register_charter(
        self,
        proposal_id: str,
        charter: AgentCharter,
        skills: list[Any],
    ) -> CapabilityProposal:
        proposal = self._get_proposal(proposal_id)
        if proposal.status != "REVIEWED":
            raise ValueError("source/license/security review must pass first")
        proposal.charter_contract = charter
        proposal.skill_contracts = skills
        return proposal

    def run_benchmark(
        self,
        proposal_id: str,
        *,
        runner: Callable[..., float],
        adversarial_runner: Callable[..., bool],
        threshold: float = 0.0,
    ) -> CapabilityProposal:
        proposal = self._get_proposal(proposal_id)
        score = self._run_agent(proposal.agent_id, proposal.agent_version, runner)
        proposal.benchmark_passed = score > threshold
        proposal.adversarial_tests_passed = self._run_agent(proposal.agent_id, proposal.agent_version, adversarial_runner)
        proposal.cost_latency_reliability = {"benchmark_score": score}

        if proposal.benchmark_passed and proposal.adversarial_tests_passed:
            proposal.status = "BENCHMARKED"
        else:
            proposal.status = "ROLLED_BACK"
        return proposal

    def run_shadow(
        self,
        proposal_id: str,
        *,
        incumbent_id: str,
        benchmark_id: str,
        metric: str,
        runner: Callable[..., float],
        baseline_runner: Callable[[], float] | None = None,
    ) -> ShadowChallenge:
        proposal = self._get_proposal(proposal_id)
        if proposal.status != "BENCHMARKED":
            raise ValueError("benchmark must pass before shadow challenge")

        incumbent_version: str | None = None
        try:
            incumbent_version = self.agents.get(incumbent_id).version
        except Exception:
            pass

        challenge = self.shadow.challenge(
            incumbent_id=incumbent_id,
            challenger_id=proposal.agent_id,
            benchmark_id=benchmark_id,
            metric=metric,
            runner=runner,
            baseline_runner=baseline_runner,
            incumbent_version=incumbent_version,
            challenger_version=proposal.agent_version,
        )
        proposal.shadow_winner = challenge.winner == "challenger"
        if challenge.status == "CHALLENGER_WINS":
            proposal.status = "SHADOW"
        else:
            proposal.status = "ROLLED_BACK"
        return challenge

    def run_canary(
        self,
        proposal_id: str,
        *,
        previous_version: str,
        scope: str,
        acceptance_criteria: dict[str, Any],
        metrics: dict[str, Any],
        eval_fn: Callable[[dict[str, Any], dict[str, Any]], bool] | None = None,
    ) -> Any:
        proposal = self._get_proposal(proposal_id)
        if proposal.status not in {"SHADOW", "BENCHMARKED"}:
            raise ValueError("shadow or benchmark must pass before canary")

        run = self.canary.start_canary(
            agent_id=proposal.agent_id,
            previous_version=previous_version,
            scope=scope,
            acceptance_criteria=acceptance_criteria,
        )
        evaluated = self.canary.evaluate_canary(run.run_id, metrics, eval_fn)
        proposal.canary_passed = evaluated.status == "PASSED"

        if proposal.canary_passed:
            proposal.status = "CANARY"
        else:
            proposal.status = "ROLLED_BACK"
            self.canary.rollback(
                agent_id=proposal.agent_id,
                new_version=proposal.agent_version,
                previous_version=previous_version,
                reason="canary acceptance criteria failed",
                details={"metrics": metrics, "criteria": acceptance_criteria},
            )
        return evaluated

    def promote(
        self,
        proposal_id: str,
        approvers: list[str],
    ) -> PromotionDecision:
        proposal = self._get_proposal(proposal_id)
        if not (proposal.canary_passed and proposal.charter_contract):
            raise ValueError("canary must pass and charter must be registered")
        if any(a == proposal.agent_id for a in approvers):
            raise ValueError("agent cannot approve its own promotion")

        previous = self.agents.lineage(proposal.agent_id)
        previous_active = previous[-2] if len(previous) >= 2 else None
        previous_version = previous_active.version if previous_active else None

        self.agents.register(proposal.charter_contract)
        decision = PromotionDecision(
            decision_id=f"PROMO-{uuid.uuid4().hex[:12]}",
            agent_id=proposal.agent_id,
            new_version=proposal.agent_version,
            previous_version=previous_version,
            approved_by=approvers,
            status="APPROVED",
        )
        self._promotions[decision.decision_id] = decision
        proposal.status = "PROMOTED"
        return decision

    def rollback(
        self,
        proposal_id: str,
        previous_version: str,
        reason: str,
    ) -> Any:
        proposal = self._get_proposal(proposal_id)
        self.agents.retire(proposal.agent_id)

        previous_charter = None
        for charter in self.agents.lineage(proposal.agent_id):
            if charter.version == previous_version:
                previous_charter = charter
                break

        if previous_charter is None:
            raise ValueError(f"previous version {previous_version} not found")

        previous_charter.status = "ACTIVE"
        self.agents.register(previous_charter)

        record = self.canary.rollback(
            agent_id=proposal.agent_id,
            new_version=proposal.agent_version,
            previous_version=previous_version,
            reason=reason,
            details={"proposal_id": proposal_id},
        )
        proposal.status = "ROLLED_BACK"
        return record

    def get_proposal(self, proposal_id: str) -> CapabilityProposal | None:
        return self._proposals.get(proposal_id)

    def _get_proposal(self, proposal_id: str) -> CapabilityProposal:
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            raise KeyError(f"Unknown proposal {proposal_id}")
        return proposal

    @staticmethod
    def _run_agent(agent_id: str, version: str | None, runner: Callable[..., Any]) -> Any:
        sig = inspect.signature(runner)
        if version is not None and len(sig.parameters) > 1:
            return runner(agent_id, version)
        return runner(agent_id)
