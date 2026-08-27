from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

from aoic_kernel.kernel import CompanyKernel
from aoic_kernel.models import (
    AgentCharter,
    Authority,
    BudgetEntry,
    CostEstimate,
    DecisionProposal,
    Evidence,
    PITRecord,
    PolicyRule,
    RiskLevel,
    Reversibility,
    ValueEstimate,
)
from aoic_kernel.loaders import load_agent_charter


@pytest.fixture
def kernel() -> CompanyKernel:
    return CompanyKernel()


@pytest.fixture
def human_principal() -> AgentCharter:
    return load_agent_charter(
        Path(__file__).parent.parent / "company" / "charters" / "human_principal.yaml"
    )


@pytest.fixture
def global_ceo() -> AgentCharter:
    return load_agent_charter(
        Path(__file__).parent.parent / "company" / "charters" / "global_ceo.yaml"
    )


@pytest.fixture
def crcso() -> AgentCharter:
    return load_agent_charter(
        Path(__file__).parent.parent / "company" / "charters" / "crcso.yaml"
    )


@pytest.fixture
def product_ceo() -> AgentCharter:
    return load_agent_charter(
        Path(__file__).parent.parent / "company" / "charters" / "product_ceo.yaml"
    )


def make_proposal(
    decision_id: str = "DEC-000001",
    proposer: str = "global_ceo@0.1.0",
    required_authority: Authority = Authority.A3,
    confidence: float | None = 0.95,
    sources: list[str] | None = None,
) -> DecisionProposal:
    return DecisionProposal(
        decision_id=decision_id,
        proposer=proposer,
        objective="Test objective",
        problem="Test problem",
        recommendation="Test recommendation",
        alternatives=["do nothing"],
        evidence=[
            Evidence(
                evidence_id="E-1",
                as_of=datetime(2026, 8, 1, tzinfo=timezone.utc),
                source=s or "sec_edgar",
                hash="abc123",
            )
            for s in (sources or ["sec_edgar"])
        ],
        expected_value=ValueEstimate(low=0, base=100, high=200, unit="EUR"),
        cost=CostEstimate(one_off=0, monthly=0, unit="EUR"),
        confidence=confidence,
        reversibility=Reversibility.HIGH,
        regulatory_risk=RiskLevel.LOW,
        required_authority=required_authority,
        rollback_plan="Revert and notify.",
    )


def make_pit_record(
    record_id: str,
    entity_id: str,
    released_at: datetime,
    as_of: datetime | None = None,
) -> PITRecord:
    return PITRecord(
        record_id=record_id,
        entity_id=entity_id,
        event_time=as_of or released_at,
        released_at=released_at,
        observed_at=released_at,
        ingested_at=released_at,
        valid_from=released_at,
        source="sec_edgar",
        data={"value": 1.0},
    )
