from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class Authority(str, Enum):
    A0 = "A0"
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    A5 = "A5"


class Reversibility(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class DecisionStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    CHALLENGED = "CHALLENGED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"
    EXECUTING = "EXECUTING"
    VERIFIED = "VERIFIED"
    ROLLED_BACK = "ROLLED_BACK"
    CLOSED = "CLOSED"


class Evidence(BaseModel):
    evidence_id: str
    as_of: datetime
    source: str
    hash: str


class ValueEstimate(BaseModel):
    low: Optional[float]
    base: Optional[float]
    high: Optional[float]
    unit: str = "EUR"


class CostEstimate(BaseModel):
    one_off: Optional[float]
    monthly: Optional[float]
    unit: str = "EUR"


class Dissent(BaseModel):
    agent_id: str
    objection: str


class DecisionProposal(BaseModel):
    decision_id: str = Field(pattern=r"^DEC-[0-9]{6}$")
    schema_version: str = "1.0"
    proposer: str = Field(pattern=r"^[a-z0-9_-]+@[0-9]+\.[0-9]+\.[0-9]+$")
    objective: str
    problem: str
    recommendation: str
    alternatives: list[str] = Field(min_length=1)
    evidence: list[Evidence]
    expected_value: ValueEstimate
    cost: CostEstimate
    confidence: Optional[float] = Field(None, ge=0, le=1)
    reversibility: Reversibility
    regulatory_risk: RiskLevel
    customer_impact: str = ""
    strategic_impact: str = ""
    urgency: str = ""
    dissent: list[Dissent] = []
    required_authority: Authority
    rollback_plan: str
    deadline: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    status: DecisionStatus = DecisionStatus.DRAFT
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    idempotency_key: Optional[str] = None

    @field_validator("expires_at")
    @classmethod
    def expires_after_now(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None:
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)
        return v


class ApprovalRecord(BaseModel):
    approval_id: str
    decision_id: str
    approver: str
    authority: Authority
    granted_at: datetime
    expires_at: Optional[datetime] = None
    scope: str = ""
    revoked: bool = False


class BudgetEntry(BaseModel):
    budget_id: str
    owner: str
    category: str
    allocated: float
    consumed: float = 0.0
    currency: str = "EUR"
    period_start: datetime
    period_end: datetime
    hard_cap: bool = True


class AgentCharter(BaseModel):
    agent_id: str = Field(pattern=r"^[a-z0-9_-]+$")
    version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    owner: str
    mission: str = Field(min_length=10)
    objectives: list[str]
    non_goals: list[str]
    inputs: list[str]
    outputs: list[str]
    tools: list[str]
    data_scopes: list[str]
    authority_level: Authority
    budgets: dict[str, Any]
    policies: list[str]
    escalation_rules: list[str]
    evaluations: list[str]
    stop_conditions: list[str]
    rollback: str
    memory_policy: str
    expiry: datetime
    status: str = "ACTIVE"


class SkillContract(BaseModel):
    skill_id: str = Field(pattern=r"^[a-z0-9_-]+$")
    version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    purpose: str = Field(min_length=10)
    preconditions: list[str]
    input_schema: str
    output_schema: str
    side_effects: list[str]
    required_permissions: list[str]
    cost_model: str
    latency_slo: str
    failure_modes: list[str]
    evidence_requirements: list[str]
    tests: list[str]
    security_classification: str
    idempotency: str
    status: str = "APPROVED"


class AOICEvent(BaseModel):
    event_id: str
    event_type: str
    timestamp: datetime
    source: str
    payload: dict[str, Any]
    causality: Optional[dict[str, Optional[str]]] = None
    signature: Optional[str] = None


class AuditEntry(BaseModel):
    entry_id: str
    timestamp: datetime
    event_type: str
    actor: str
    action: str
    target: str
    outcome: str
    details: dict[str, Any] = {}
    previous_hash: Optional[str] = None
    hash: Optional[str] = None


class PITRecord(BaseModel):
    record_id: str
    entity_id: str
    event_time: datetime
    released_at: datetime
    observed_at: datetime
    ingested_at: datetime
    valid_from: datetime
    valid_to: Optional[datetime] = None
    source: str
    source_version: Optional[str] = None
    content_hash: Optional[str] = None
    data: dict[str, Any]

    def is_available_at(self, as_of: datetime) -> bool:
        if self.valid_to is not None and as_of >= self.valid_to:
            return False
        return as_of >= self.valid_from


class PolicyRule(BaseModel):
    policy_id: str
    version: str
    applies_to: list[str]
    condition: str
    effect: str  # ALLOW, DENY, ESCALATE
    authority_min: Authority


class Incident(BaseModel):
    incident_id: str
    severity: str
    detected_at: datetime
    description: str
    status: str
    owner: str
