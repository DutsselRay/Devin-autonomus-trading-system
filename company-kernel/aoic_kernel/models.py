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
    one_off: Optional[float] = None
    monthly: Optional[float] = None
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


class CapabilityProposal(BaseModel):
    proposal_id: str
    agent_id: str
    agent_version: str
    proposer: str
    capability_gap: str
    expected_value: dict[str, Any] = Field(default_factory=dict)
    source_reviewed: bool = False
    license_approved: bool = False
    security_reviewed: bool = False
    charter_contract: Optional[AgentCharter] = None
    skill_contracts: list[SkillContract] = Field(default_factory=list)
    benchmark_passed: bool = False
    adversarial_tests_passed: bool = False
    cost_latency_reliability: dict[str, Any] = Field(default_factory=dict)
    shadow_winner: bool = False
    canary_passed: bool = False
    status: str = "PROPOSED"  # PROPOSED, REVIEWED, BENCHMARKED, SHADOW, CANARY, PROMOTED, ROLLED_BACK, RETIRED


class ShadowChallenge(BaseModel):
    challenge_id: str
    incumbent_id: str
    challenger_id: str
    benchmark_id: str
    metric: str
    incumbent_score: float
    challenger_score: float
    baseline_score: float
    winner: str  # incumbent, challenger, baseline, none
    status: str = "RUNNING"  # RUNNING, CHALLENGER_WINS, INCUMBENT_WINS, TIE


class CanaryRun(BaseModel):
    run_id: str
    agent_id: str
    previous_version: Optional[str] = None
    scope: str
    start_time: datetime
    end_time: Optional[datetime] = None
    acceptance_criteria: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    status: str = "RUNNING"  # RUNNING, PASSED, FAILED


class RollbackRecord(BaseModel):
    rollback_id: str
    agent_id: str
    triggered_at: datetime
    reason: str
    previous_version: str
    new_version: str
    details: dict[str, Any] = Field(default_factory=dict)


class PromotionDecision(BaseModel):
    decision_id: str
    agent_id: str
    new_version: str
    previous_version: Optional[str] = None
    approved_by: list[str] = Field(default_factory=list)
    status: str = "PENDING"  # PENDING, APPROVED, DENIED


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, Enum):
    DETECTED = "DETECTED"
    CLASSIFIED = "CLASSIFIED"
    CONTAINED = "CONTAINED"
    EVIDENCE_PRESERVED = "EVIDENCE_PRESERVED"
    NOTIFIED = "NOTIFIED"
    RECOVERING = "RECOVERING"
    VERIFIED = "VERIFIED"
    POSTMORTEM = "POSTMORTEM"
    REMEDIATED = "REMEDIATED"
    CLOSED = "CLOSED"


class Incident(BaseModel):
    incident_id: str
    title: str
    description: str
    severity: Severity
    status: IncidentStatus = IncidentStatus.DETECTED
    detected_at: datetime
    contained_at: Optional[datetime] = None
    recovered_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    postmortem_at: Optional[datetime] = None
    remediated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    evidence: list[str] = Field(default_factory=list)
    notifications: list[str] = Field(default_factory=list)
    postmortem_report: Optional[str] = None
    remediation_plan: Optional[str] = None


class LivePredictionStatus(str, Enum):
    SEALED = "SEALED"
    RELEASED = "RELEASED"
    RESOLVED = "RESOLVED"


class LivePrediction(BaseModel):
    prediction_id: str
    entity_id: str
    feature_name: str
    horizon: timedelta
    predicted_value: Any
    probability: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    created_at: datetime
    release_at: datetime
    released_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    actual_value: Optional[Any] = None
    status: LivePredictionStatus = LivePredictionStatus.SEALED
    audit_log_id: Optional[str] = None


class DashboardSnapshot(BaseModel):
    snapshot_at: datetime
    pending_decisions: list[DecisionProposal] = Field(default_factory=list)
    released_predictions: list[LivePrediction] = Field(default_factory=list)
    active_incidents: list[Incident] = Field(default_factory=list)
    attention_score: dict[str, Any] = Field(default_factory=dict)
    audit_summary: dict[str, int] = Field(default_factory=dict)


class LaunchGateStatus(str, Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    WAIVED = "WAIVED"


class LaunchGate(BaseModel):
    gate_id: str
    name: str
    status: LaunchGateStatus
    evidence: list[str] = Field(default_factory=list)
    reviewed_by: str
    reviewed_at: datetime
    expires_at: Optional[datetime] = None


class CustomerSubscription(BaseModel):
    subscription_id: str
    customer_id: str
    plan: str
    status: str = "ACTIVE"  # ACTIVE, SUSPENDED, CANCELLED
    start_date: datetime
    billing_cycle: str = "monthly"
    price: float
    currency: str = "EUR"


class SupportTicket(BaseModel):
    ticket_id: str
    customer_id: str
    subject: str
    severity: str
    status: str = "OPEN"  # OPEN, PENDING, RESOLVED, CLOSED
    created_at: datetime
    resolved_at: Optional[datetime] = None
    evidence_links: list[str] = Field(default_factory=list)


class TrackRecordEntry(BaseModel):
    entry_id: str
    prediction_id: str
    entity_id: str
    predicted_value: Any
    actual_value: Any
    probability: float
    release_at: datetime
    resolved_at: datetime
    evidence: list[str] = Field(default_factory=list)
    claim: str


class LaunchDecision(BaseModel):
    decision_id: str
    status: str = "PENDING"  # PENDING, APPROVED, DENIED
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    gates: list[str] = Field(default_factory=list)
    rationale: str = ""


class MaturityLevel(str, Enum):
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"
    PASS = "PASS"


class MaturityCriterion(BaseModel):
    criterion_id: str
    name: str
    description: str
    level: MaturityLevel = MaturityLevel.FAIL
    evidence: list[str] = Field(default_factory=list)
    updated_at: Optional[datetime] = None


class MaturityScore(BaseModel):
    scorecard_id: str
    evaluated_at: datetime
    criteria: list[MaturityCriterion] = Field(default_factory=list)
    overall_10_of_10: bool = False
    average: Optional[float] = None


class CampaignStatus(str, Enum):
    DRAFT = "DRAFT"
    REVIEWED = "REVIEWED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class GrowthCampaign(BaseModel):
    campaign_id: str
    name: str
    channel: str
    status: CampaignStatus = CampaignStatus.DRAFT
    audience: str
    budget: float
    start_date: datetime
    end_date: Optional[datetime] = None
    leads: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    created_at: datetime


class ProcurementStatus(str, Enum):
    DRAFT = "DRAFT"
    VENDOR_REVIEW = "VENDOR_REVIEW"
    SECURITY_REVIEW = "SECURITY_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"


class ProcurementRequest(BaseModel):
    request_id: str
    vendor_name: str
    purpose: str
    amount: float
    recurring: bool = False
    status: ProcurementStatus = ProcurementStatus.DRAFT
    requested_by: str
    evidence: list[str] = Field(default_factory=list)
    created_at: datetime
    approved_by: list[str] = Field(default_factory=list)


class AuditFinding(BaseModel):
    finding_id: str
    scope: str
    severity: RiskLevel
    description: str
    evidence: list[str] = Field(default_factory=list)
    auditor: str
    reported_at: datetime
    status: str = "OPEN"  # OPEN, ACCEPTED, REMEDIATED, DISPUTED


class RedTeamExercise(BaseModel):
    exercise_id: str
    target_system: str
    objective: str
    team: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)
    status: str = "PLANNED"  # PLANNED, RUNNING, COMPLETED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class B2BProductGateStatus(str, Enum):
    BLOCKED = "BLOCKED"
    V1_PROOF = "V1_PROOF"
    APPROVED = "APPROVED"


class B2BProductGate(BaseModel):
    product_id: str
    name: str
    status: B2BProductGateStatus = B2BProductGateStatus.BLOCKED
    v1_proof_evidence: list[str] = Field(default_factory=list)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


class ConnectorStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    DISABLED = "DISABLED"


class SourceConnector(BaseModel):
    connector_id: str
    name: str
    vendor: str
    purpose: str
    auth_type: str
    rate_limit: str
    rights: str
    provenance: str
    pit_semantics: str
    quality_checks: list[str] = Field(default_factory=list)
    cost: CostEstimate
    fallback_connector: Optional[str] = None
    status: ConnectorStatus = ConnectorStatus.ACTIVE
    registered_at: datetime


class VendorStatus(str, Enum):
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    EXPIRING = "EXPIRING"
    EXITED = "EXITED"


class Vendor(BaseModel):
    vendor_id: str
    name: str
    purpose: str
    owner: str
    spend: float = 0.0
    renewal_date: Optional[datetime] = None
    alternatives: list[str] = Field(default_factory=list)
    data_classification: str = "internal"
    subprocessors: list[str] = Field(default_factory=list)
    sla: str = ""
    exit_plan: str = ""
    rights: str = ""
    status: VendorStatus = VendorStatus.ACTIVE
    registered_at: datetime


class ModelProviderStatus(str, Enum):
    ACTIVE = "ACTIVE"
    KILLED = "KILLED"


class ModelProvider(BaseModel):
    provider_id: str
    name: str
    model_family: str
    cost_per_1k_tokens: float
    status: ModelProviderStatus = ModelProviderStatus.ACTIVE
    max_rpm: int = 60
    registered_at: datetime
