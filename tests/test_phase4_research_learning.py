from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from aoic_kernel.kernel import CompanyKernel
from aoic_kernel.models import (
    CommitteeReview,
    CommitteeRole,
    Entity,
    Pattern,
    PatternStatus,
    Prediction,
    ResearchOpportunity,
)


def _day(n: int) -> datetime:
    return datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(days=n)


def _feature(
    entity_id: str,
    feature_name: str,
    event_time: datetime,
    released_at: datetime,
    value: float,
) -> Any:
    from aoic_kernel.models import FeatureRecord

    return FeatureRecord(
        record_id=f"FEAT-{entity_id}-{feature_name}-{event_time:%Y%m%d}",
        entity_id=entity_id,
        feature_name=feature_name,
        event_time=event_time,
        released_at=released_at,
        observed_at=released_at,
        ingested_at=released_at,
        valid_from=event_time,
        value=value,
        source="test",
    )


def _pattern(
    pattern_id: str = "PAT-000001",
    eligible: list[str] | None = None,
    status: PatternStatus = PatternStatus.IDEA,
) -> Pattern:
    return Pattern(
        pattern_id=pattern_id,
        name="momentum",
        version="0.1.0",
        eligible_universe=eligible or ["AAPL_US", "MSFT_US"],
        regime="bull",
        feature_predicate="price > 100",
        economic_rationale="positive momentum persists",
        prediction="return > 0 over horizon",
        horizon="5d",
        success_label="return > 0",
        status=status,
    )


def _opportunity(
    opportunity_id: str = "OPP-000001",
    probability: float = 0.92,
    sample_size: int = 40,
    reviews: list[CommitteeReview] | None = None,
) -> ResearchOpportunity:
    return ResearchOpportunity(
        opportunity_id=opportunity_id,
        entity_id="AAPL_US",
        pattern_id="PAT-000001",
        as_of=_day(0),
        probability=probability,
        expected_return=0.05,
        downside=-0.02,
        invalidation_conditions=["price below support"],
        regime="bull",
        status="COMMITTEE_REVIEW",
        committee_reviews=reviews or [],
        sample_size=sample_size,
    )


def _review(role: CommitteeRole, score: float, dissent: str | None = None) -> CommitteeReview:
    return CommitteeReview(
        review_id=f"REV-{role.value}",
        pattern_id="PAT-000001",
        role=role,
        reviewer=role.value.lower(),
        score=score,
        dissent=dissent,
    )


# 1. Pattern lifecycle with valid promotion path.
def test_pattern_lifecycle(kernel: CompanyKernel) -> None:
    pattern = _pattern()
    kernel.opportunity.patterns.register(pattern)
    assert pattern.status == PatternStatus.IDEA

    kernel.opportunity.patterns.promote(pattern.pattern_id, PatternStatus.DISCOVERED)
    assert pattern.status == PatternStatus.DISCOVERED

    kernel.opportunity.patterns.promote(pattern.pattern_id, PatternStatus.REPLICATED)
    kernel.opportunity.patterns.promote(pattern.pattern_id, PatternStatus.SEALED_OOS)
    assert pattern.status == PatternStatus.SEALED_OOS

    with pytest.raises(ValueError):
        kernel.opportunity.patterns.promote(pattern.pattern_id, PatternStatus.IDEA)


# 2. Pattern eligibility restricted to declared universe.
def test_pattern_eligibility(kernel: CompanyKernel) -> None:
    pattern = _pattern(eligible=["AAPL_US"])
    kernel.opportunity.patterns.register(pattern)

    assert kernel.opportunity.patterns.eligible_for_entity("PAT-000001", "AAPL_US")
    assert not kernel.opportunity.patterns.eligible_for_entity("PAT-000001", "MSFT_US")


# 3. Retired pattern cannot screen entities.
def test_retired_pattern_not_eligible(kernel: CompanyKernel) -> None:
    pattern = _pattern(eligible=["AAPL_US"])
    kernel.opportunity.patterns.register(pattern)
    kernel.opportunity.patterns.retire(pattern.pattern_id, "failed replication")

    assert not kernel.opportunity.patterns.eligible_for_entity("PAT-000001", "AAPL_US")


# 4. Research funnel screens and triages candidates deterministically.
def test_research_funnel_screen_and_triage(kernel: CompanyKernel) -> None:
    kernel.opportunity.entity_master.register(
        Entity(
            entity_id="AAPL_US",
            symbol="AAPL",
            name="Apple",
            asset_class="equity",
        )
    )
    kernel.opportunity.entity_master.register(
        Entity(
            entity_id="MSFT_US",
            symbol="MSFT",
            name="Microsoft",
            asset_class="equity",
        )
    )

    for i in range(3):
        kernel.opportunity.feature_store.store(_feature("AAPL_US", "momentum", _day(i), _day(i), 1.5))
        kernel.opportunity.feature_store.store(_feature("MSFT_US", "momentum", _day(i), _day(i), 0.5))

    pattern = _pattern(eligible=["AAPL_US", "MSFT_US"])
    kernel.opportunity.patterns.register(pattern)

    def predicate(entity_id: str, as_of: datetime, fs) -> bool:
        record = fs.get(entity_id, "momentum", as_of)
        return record is not None and record.value > 1.0

    screened = kernel.opportunity.research.screen(["AAPL_US", "MSFT_US"], _day(2), predicate)
    assert screened == ["AAPL_US"]

    triaged = kernel.opportunity.research.triage(screened, _day(2), pattern.pattern_id)
    assert len(triaged) == 1
    assert triaged[0].entity_id == "AAPL_US"


# 5. Adversarial committee reviews aggregate and preserve dissent.
def test_adversarial_committee_review(kernel: CompanyKernel) -> None:
    opportunity = _opportunity(reviews=[])
    reviews = [
        _review(CommitteeRole.BULL, 0.8),
        _review(CommitteeRole.BEAR, -0.2, dissent="valuation stretched"),
        _review(CommitteeRole.RISK, 0.1),
    ]
    reviewed = kernel.opportunity.research.committee_review(opportunity, reviews)
    assert len(reviewed.committee_reviews) == 3
    assert reviewed.committee_reviews[1].dissent == "valuation stretched"
    expected_score = (0.8 - 0.2 + 0.1) / 3
    assert kernel.opportunity.research.committee_score(reviewed) == pytest.approx(expected_score, abs=1e-9)


# 6. Publication gate passes with calibrated probability > 0.90.
def test_publication_gate_passes(kernel: CompanyKernel) -> None:
    scores = [(0.9 if i % 2 == 0 else 0.1, float(i % 2)) for i in range(40)]
    kernel.opportunity.calibration.fit("CAL-000001", "v1", scores)

    opportunity = _opportunity(
        reviews=[
            _review(CommitteeRole.BULL, 0.8),
            _review(CommitteeRole.BEAR, 0.2),
            _review(CommitteeRole.RISK, 0.4),
            _review(CommitteeRole.VALUATION, 0.5),
            _review(CommitteeRole.EVIDENCE, 0.6),
            _review(CommitteeRole.JUDGE, 0.7),
        ]
    )

    result = kernel.opportunity.publication.evaluate(opportunity, calibration_id="CAL-000001")
    assert result["status"] == "PASS"
    assert opportunity.status == "PUBLISHED"


# 7. Publication gate abstains when probability is below the gate.
def test_publication_gate_abstains_low_probability(kernel: CompanyKernel) -> None:
    scores = [(0.9 if i % 2 == 0 else 0.1, float(i % 2)) for i in range(40)]
    kernel.opportunity.calibration.fit("CAL-000002", "v1", scores)

    opportunity = _opportunity(probability=0.85)
    result = kernel.opportunity.publication.evaluate(opportunity, calibration_id="CAL-000002")
    assert result["status"] == "ABSTAIN"
    assert "probability" in str(result["reasons"])


# 8. Publication gate abstains when sample size is too small.
def test_publication_gate_abstains_small_sample(kernel: CompanyKernel) -> None:
    opportunity = _opportunity(probability=0.95, sample_size=5)
    result = kernel.opportunity.publication.evaluate(opportunity)
    assert result["status"] == "ABSTAIN"
    assert "sample size" in str(result["reasons"])


# 9. Publication gate abstains on calibration drift or insufficiency.
def test_publication_gate_abstains_calibration_issues(kernel: CompanyKernel) -> None:
    opportunity = _opportunity(probability=0.95, sample_size=40)
    # Missing calibration run.
    result = kernel.opportunity.publication.evaluate(opportunity, calibration_id="CAL-MISSING")
    assert result["status"] == "ABSTAIN"
    assert "calibration" in str(result["reasons"])

    # Insufficient calibration.
    kernel.opportunity.calibration.fit("CAL-000003", "v1", [(0.9, 1.0)])
    result2 = kernel.opportunity.publication.evaluate(opportunity, calibration_id="CAL-000003")
    assert result2["status"] == "ABSTAIN"
    assert "insufficient" in str(result2["reasons"]).lower()


# 10. Calibration engine computes Brier and expected calibration error.
def test_calibration_engine_metrics(kernel: CompanyKernel) -> None:
    # Perfectly calibrated: probabilities match outcomes.
    scores = [(0.9, 1.0), (0.9, 1.0), (0.1, 0.0), (0.1, 0.0)] * 10
    run = kernel.opportunity.calibration.fit("CAL-000004", "v1", scores)
    assert run.brier_score is not None
    assert run.expected_calibration_error is not None
    assert run.log_loss is not None
    assert 0 <= run.brier_score <= 1


# 11. Outcome engine attributes predictions and computes hit rate.
def test_outcome_attribution_and_hit_rate(kernel: CompanyKernel) -> None:
    pred_a = Prediction(
        prediction_id="PRED-000001",
        entity_id="AAPL_US",
        as_of=_day(0),
        horizon="5d",
        probability=0.92,
    )
    pred_b = Prediction(
        prediction_id="PRED-000002",
        entity_id="MSFT_US",
        as_of=_day(0),
        horizon="5d",
        probability=0.85,
    )

    kernel.opportunity.outcomes.record_outcome("OUT-000001", pred_a, _day(5), actual_return=0.05)
    kernel.opportunity.outcomes.record_outcome("OUT-000002", pred_b, _day(5), actual_return=-0.01)

    hit_rate = kernel.opportunity.outcomes.hit_rate(list(kernel.opportunity.outcomes._outcomes.values()))
    assert hit_rate == 0.5

    brier = kernel.opportunity.outcomes.brier_score([pred_a, pred_b], list(kernel.opportunity.outcomes._outcomes.values()))
    assert brier is not None
    assert brier >= 0


# 12. Durable learning requires replication and minimum evidence.
def test_durable_learning_promotion_gated(kernel: CompanyKernel) -> None:
    evidence = [f"evidence-{i}" for i in range(30)]
    learning = kernel.opportunity.outcomes.propose_learning(
        learning_id="LEARN-000001",
        pattern_id="PAT-000001",
        experiment_id="EXP-000001",
        hypothesis="momentum works in bull regimes",
        evidence=evidence,
        replicators=["cao_auditor"],
    )
    assert learning is not None
    assert learning.status == "REPLICATED"

    not_learning = kernel.opportunity.outcomes.propose_learning(
        learning_id="LEARN-000002",
        pattern_id="PAT-000001",
        experiment_id="EXP-000001",
        hypothesis="too little evidence",
        evidence=evidence[:5],
        replicators=["cao_auditor"],
    )
    assert not_learning is None
