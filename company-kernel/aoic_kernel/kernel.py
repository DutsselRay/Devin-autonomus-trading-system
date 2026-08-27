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
from aoic_kernel.shadow_challenger import ShadowChallenger
from aoic_kernel.canary_rollback import CanaryRollback
from aoic_kernel.agent_lifecycle import AgentLifecycle
from aoic_kernel.live_prediction import LivePredictionRegistry
from aoic_kernel.incident_engine import IncidentEngine
from aoic_kernel.dashboard import InternalDashboard, AuditView
from aoic_kernel.commercial_readiness import CommercialReadiness
from aoic_kernel.public_track_record import PublicTrackRecord
from aoic_kernel.billing_support import BillingSupport
from aoic_kernel.a5_launch import A5Launch, CustomerWeb
from aoic_kernel.cmo_growth import CMOGrowth
from aoic_kernel.procurement import Procurement
from aoic_kernel.enterprise_audit import EnterpriseAuditor
from aoic_kernel.red_team import RedTeam
from aoic_kernel.b2b_gate import B2BGate
from aoic_kernel.maturity_evaluator import MaturityEvaluator
from aoic_kernel.source_adapter import SourceAdapter
from aoic_kernel.vendor_register import VendorRegister
from aoic_kernel.model_gateway import ModelGateway


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
        self.shadow = ShadowChallenger(self.evals)
        self.canary = CanaryRollback()
        self.agent_lifecycle = AgentLifecycle(
            agent_registry=self.agents,
            skill_registry=self.skills,
            shadow_challenger=self.shadow,
            canary_rollback=self.canary,
        )
        self.live_predictions = LivePredictionRegistry()
        self.incidents = IncidentEngine()
        self.dashboard = InternalDashboard(
            audit=self.audit,
            attention=self.attention,
            live_predictions=self.live_predictions,
            incidents=self.incidents,
        )
        self.audit_view = AuditView(self.audit)
        self.commercial_readiness = CommercialReadiness()
        self.public_track_record = PublicTrackRecord(self.live_predictions)
        self.billing_support = BillingSupport()
        self.a5_launch = A5Launch(self.commercial_readiness)
        self.customer_web = CustomerWeb(self.public_track_record)
        self.cmo_growth = CMOGrowth()
        self.procurement = Procurement()
        self.enterprise_audit = EnterpriseAuditor()
        self.red_team = RedTeam()
        self.b2b_gate = B2BGate()
        self.maturity = MaturityEvaluator()
        self.source_adapter = SourceAdapter()
        self.vendor_register = VendorRegister()
        self.model_gateway = ModelGateway()
