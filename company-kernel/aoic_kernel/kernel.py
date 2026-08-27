from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aoic_kernel.audit_log import ImmutableAuditLog
from aoic_kernel.authority_engine import AuthorityEngine
from aoic_kernel.approval_engine import ApprovalEngine
from aoic_kernel.budget_engine import BudgetEngine
from aoic_kernel.policy_engine import PolicyEngine
from aoic_kernel.agent_registry import AgentRegistry
from aoic_kernel.skill_registry import SkillRegistry
from aoic_kernel.memory_engine import MemoryEngine
from aoic_kernel.eval_engine import EvalEngine
from aoic_kernel.event_bus import EventBus
from aoic_kernel.task_router import TaskRouter
from aoic_kernel.decision_engine import DecisionEngine
from aoic_kernel.publication_gate import PublicationGate
from aoic_kernel.daily_briefing import DailyBriefing, HumanAttentionScore
from aoic_kernel.opportunity_engine import OpportunityEngine


class CompanyKernel:
    """Deterministic infrastructure around probabilistic agents."""

    def __init__(self) -> None:
        self.audit = ImmutableAuditLog()
        self.authority = AuthorityEngine()
        self.approval = ApprovalEngine()
        self.budget = BudgetEngine()
        self.policy = PolicyEngine()
        self.agents = AgentRegistry()
        self.skills = SkillRegistry()
        self.memory = MemoryEngine()
        self.evals = EvalEngine()
        self.events = EventBus()
        self.tasks = TaskRouter()
        self.decisions = DecisionEngine(
            authority=self.authority,
            approval=self.approval,
            budget=self.budget,
            policy=self.policy,
            audit=self.audit,
        )
        self.publication = PublicationGate(
            policy=self.policy,
            audit=self.audit,
        )
        self.attention = HumanAttentionScore()
        self.briefing = DailyBriefing(self.attention)
        self.opportunity = OpportunityEngine()
