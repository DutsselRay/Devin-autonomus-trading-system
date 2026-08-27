from __future__ import annotations

from datetime import datetime, timedelta, timezone
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


class Entity(BaseModel):
    entity_id: str = Field(pattern=r"^[A-Z0-9_-]+$")
    symbol: str
    name: str
    asset_class: str = "equity"
    primary_exchange: Optional[str] = None
    list_date: Optional[datetime] = None
    delist_date: Optional[datetime] = None
    status: str = "ACTIVE"

    def is_active_as_of(self, as_of: datetime) -> bool:
        if self.list_date is not None and as_of < self.list_date:
            return False
        if self.delist_date is not None and as_of >= self.delist_date:
            return False
        return True


class FeatureRecord(BaseModel):
    record_id: str
    entity_id: str
    feature_name: str
    event_time: datetime
    released_at: datetime
    observed_at: datetime
    ingested_at: datetime
    valid_from: datetime
    valid_to: Optional[datetime] = None
    value: Any
    unit: Optional[str] = None
    source: str
    source_version: Optional[str] = None
    transformation_version: Optional[str] = None
    availability_delay: Optional[float] = 0.0
    quality_flags: list[str] = Field(default_factory=list)
    content_hash: Optional[str] = None

    def available_at(self) -> datetime:
        return self.released_at + timedelta(seconds=self.availability_delay or 0)

    def is_available_at(self, as_of: datetime) -> bool:
        if as_of < self.available_at():
            return False
        if self.valid_to is not None and as_of >= self.valid_to:
            return False
        return as_of >= self.valid_from


class ExperimentStatus(str, Enum):
    PREREGISTERED = "PREREGISTERED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SEALED_OOS = "SEALED_OOS"


class Experiment(BaseModel):
    experiment_id: str = Field(pattern=r"^EXP-[0-9]{6}$")
    name: str
    hypothesis: str
    status: ExperimentStatus = ExperimentStatus.PREREGISTERED
    discoverer: str
    auditor: Optional[str] = None
    discovery_start: datetime
    discovery_end: datetime
    oos_set_id: Optional[str] = None
    backtest_id: Optional[str] = None
    contamination_log: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Prediction(BaseModel):
    prediction_id: str
    entity_id: str
    as_of: datetime
    horizon: str
    probability: float = Field(ge=0, le=1)
    expected_return: Optional[float] = None
    benchmark: Optional[str] = None
    source_experiment: Optional[str] = None


class BacktestRun(BaseModel):
    backtest_id: str
    experiment_id: Optional[str] = None
    strategy: str
    universe: list[str]
    start_date: datetime
    end_date: datetime
    start_value: float
    end_value: float
    costs: float
    benchmark: str
    metrics: dict[str, Any] = Field(default_factory=dict)

    @property
    def total_return(self) -> float:
        if self.start_value == 0:
            return 0.0
        return (self.end_value - self.costs) / self.start_value - 1.0


class PatternStatus(str, Enum):
    IDEA = "IDEA"
    DISCOVERED = "DISCOVERED"
    REPLICATED = "REPLICATED"
    SEALED_OOS = "SEALED_OOS"
    SHADOW_LIVE = "SHADOW_LIVE"
    ELIGIBLE = "ELIGIBLE"
    RETIRED = "RETIRED"


class Pattern(BaseModel):
    pattern_id: str = Field(pattern=r"^PAT-[0-9]{6}$")
    name: str
    version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    eligible_universe: list[str]
    regime: str
    feature_predicate: str
    economic_rationale: str
    prediction: str
    horizon: str
    success_label: str
    discovery_samples: list[str] = Field(default_factory=list)
    validation_samples: list[str] = Field(default_factory=list)
    confounders: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
    effect_size: Optional[float] = None
    uncertainty: Optional[float] = None
    capacity: Optional[float] = None
    transaction_costs: float = 0.0
    liquidity_assumptions: str = ""
    parent_pattern_id: Optional[str] = None
    child_pattern_ids: list[str] = Field(default_factory=list)
    experiment_ids: list[str] = Field(default_factory=list)
    status: PatternStatus = PatternStatus.IDEA
    metadata: dict[str, Any] = Field(default_factory=dict)


class CommitteeRole(str, Enum):
    BULL = "BULL"
    BEAR = "BEAR"
    RISK = "RISK"
    VALUATION = "VALUATION"
    EVIDENCE = "EVIDENCE"
    JUDGE = "JUDGE"


class CommitteeReview(BaseModel):
    review_id: str
    pattern_id: str
    role: CommitteeRole
    reviewer: str
    score: float = Field(ge=-1, le=1)
    dissent: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResearchOpportunity(BaseModel):
    opportunity_id: str
    entity_id: str
    pattern_id: str
    as_of: datetime
    probability: float = Field(ge=0, le=1)
    expected_return: Optional[float] = None
    downside: Optional[float] = None
    invalidation_conditions: list[str] = Field(default_factory=list)
    regime: str
    status: str = "CANDIDATE"  # CANDIDATE, TRIAGED, DEEP_RESEARCH, COMMITTEE_REVIEW, PUBLISHED, ABSTAINED
    committee_reviews: list[CommitteeReview] = Field(default_factory=list)
    calibration_score: Optional[float] = None
    sample_size: Optional[int] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CalibrationRun(BaseModel):
    calibration_id: str
    model_version: str
    fitted_at: datetime
    scores: list[tuple[float, float]] = Field(default_factory=list)  # (prediction, outcome)
    brier_score: Optional[float] = None
    expected_calibration_error: Optional[float] = None
    log_loss: Optional[float] = None
    bucket_metrics: dict[str, Any] = Field(default_factory=dict)
    status: str = "VALID"  # VALID, DRIFT, INSUFFICIENT


class Outcome(BaseModel):
    outcome_id: str
    prediction_id: Optional[str] = None
    entity_id: str
    as_of: datetime
    horizon: str
    observed_at: datetime
    actual_return: Optional[float] = None
    hit: Optional[bool] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DurableLearning(BaseModel):
    learning_id: str
    pattern_id: Optional[str] = None
    experiment_id: Optional[str] = None
    hypothesis: str
    evidence: list[str] = Field(default_factory=list)
    effective_sample_size: int = 0
    validated_by: list[str] = Field(default_factory=list)
    status: str = "PROPOSED"  # PROPOSED, REPLICATED, APPROVED, RETIRED
