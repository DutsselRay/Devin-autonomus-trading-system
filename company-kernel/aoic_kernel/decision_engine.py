from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aoic_kernel.models import AgentCharter, Authority, DecisionProposal, DecisionStatus
from aoic_kernel.authority_engine import AuthorityEngine
from aoic_kernel.approval_engine import ApprovalEngine
from aoic_kernel.budget_engine import BudgetEngine
from aoic_kernel.policy_engine import PolicyEngine
from aoic_kernel.audit_log import ImmutableAuditLog
from aoic_kernel.exceptions import AOICError


class DecisionEngine:
    """Validates and scores DecisionProposal objects through the kernel."""

    def __init__(
        self,
        authority: AuthorityEngine,
        approval: ApprovalEngine,
        budget: BudgetEngine,
        policy: PolicyEngine,
        audit: ImmutableAuditLog,
    ) -> None:
        self.authority = authority
        self.approval = approval
        self.budget = budget
        self.policy = policy
        self.audit = audit

    def _next_audit_id(self) -> str:
        return f"AUD-{len(self.audit.entries)+1:06d}"

    def submit(self, charter: AgentCharter, proposal: DecisionProposal) -> DecisionProposal:
        """Submit a proposal for validation; does not execute."""
        try:
            self.authority.check(charter, proposal)
            self.policy.evaluate(proposal)
            proposal.status = DecisionStatus.VALIDATED
            self.audit.append(
                entry_id=self._next_audit_id(),
                event_type="DECISION_VALIDATED",
                actor=charter.agent_id,
                action="validate",
                target=proposal.decision_id,
                outcome="PASS",
                details={"required_authority": proposal.required_authority},
            )
        except AOICError as e:
            proposal.status = DecisionStatus.REJECTED
            self.audit.append(
                entry_id=self._next_audit_id(),
                event_type="DECISION_REJECTED",
                actor=charter.agent_id,
                action="validate",
                target=proposal.decision_id,
                outcome="FAIL",
                details={"reason": str(e)},
            )
            raise
        return proposal

    def approve(
        self,
        approver: AgentCharter,
        proposal: DecisionProposal,
        approval_id: str,
        expires_at: datetime | None = None,
    ) -> DecisionProposal:
        self.authority.check(approver, proposal, current_authority=approver.authority_level)
        self.approval.request(
            approval_id=approval_id,
            decision_id=proposal.decision_id,
            approver=approver.agent_id,
            authority=proposal.required_authority,
            expires_at=expires_at,
        )
        proposal.status = DecisionStatus.APPROVED
        proposal.approved_by = approver.agent_id
        proposal.approved_at = datetime.now(timezone.utc)
        return proposal

    def execute(
        self,
        charter: AgentCharter,
        proposal: DecisionProposal,
        approval_id: str,
        budget_id: str,
        cost: float,
        idempotency_key: str | None = None,
    ) -> DecisionProposal:
        self.authority.check(charter, proposal)
        self.approval.validate(approval_id, proposal.decision_id)
        self.budget.check_action(budget_id, cost, proposal.recommendation, idempotency_key)
        proposal.status = DecisionStatus.EXECUTING
        proposal.executed_at = datetime.now(timezone.utc)
        return proposal
