from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from aoic_kernel.models import (
    CommitteeReview,
    CommitteeRole,
    FeatureRecord,
    ResearchOpportunity,
)
from aoic_kernel.pattern_engine import PatternEngine
from aoic_kernel.feature_store import TemporalFeatureStore


class ResearchEngine:
    """Cost-aware research funnel and adversarial investment committee."""

    def __init__(
        self,
        pattern_engine: PatternEngine,
        feature_store: TemporalFeatureStore,
    ) -> None:
        self.pattern_engine = pattern_engine
        self.feature_store = feature_store
        self._opportunities: dict[str, ResearchOpportunity] = {}

    def screen(
        self,
        universe: list[str],
        as_of: datetime,
        predicate: Callable[[str, datetime, TemporalFeatureStore], bool],
    ) -> list[str]:
        """Deterministic filter over the universe."""
        return [entity_id for entity_id in universe if predicate(entity_id, as_of, self.feature_store)]

    def triage(
        self,
        candidates: list[str],
        as_of: datetime,
        pattern_id: str,
        max_candidates: int = 10,
        scorer: Callable[[str, datetime, TemporalFeatureStore], float] | None = None,
    ) -> list[ResearchOpportunity]:
        """Select top candidates for deep research."""
        pattern = self.pattern_engine.get(pattern_id)
        if pattern is None:
            raise ValueError(f"Unknown pattern {pattern_id}")

        scored = [
            (entity_id, scorer(entity_id, as_of, self.feature_store) if scorer else 0.0)
            for entity_id in candidates
            if self.pattern_engine.eligible_for_entity(pattern_id, entity_id)
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:max_candidates]

        opportunities: list[ResearchOpportunity] = []
        for entity_id, score in top:
            opportunity = ResearchOpportunity(
                opportunity_id=f"OPP-{uuid.uuid4().hex[:12]}",
                entity_id=entity_id,
                pattern_id=pattern_id,
                as_of=as_of,
                probability=0.5,  # uncalibrated placeholder
                expected_return=None,
                regime=pattern.regime,
                status="TRIAGED",
                metadata={"triage_score": score},
            )
            self._opportunities[opportunity.opportunity_id] = opportunity
            opportunities.append(opportunity)
        return opportunities

    def deep_research(
        self,
        opportunity: ResearchOpportunity,
        *,
        probability: float,
        expected_return: float,
        downside: float,
        invalidation_conditions: list[str],
        sample_size: int,
    ) -> ResearchOpportunity:
        opportunity.probability = probability
        opportunity.expected_return = expected_return
        opportunity.downside = downside
        opportunity.invalidation_conditions = invalidation_conditions
        opportunity.sample_size = sample_size
        opportunity.status = "DEEP_RESEARCH"
        return opportunity

    def committee_review(
        self,
        opportunity: ResearchOpportunity,
        reviews: list[CommitteeReview],
    ) -> ResearchOpportunity:
        """Aggregate independent committee reviews and preserve dissent."""
        opportunity.committee_reviews = reviews
        opportunity.status = "COMMITTEE_REVIEW"
        return opportunity

    def committee_score(self, opportunity: ResearchOpportunity) -> float:
        """Return Judge score, or average if no Judge present."""
        judge_reviews = [
            r for r in opportunity.committee_reviews if r.role == CommitteeRole.JUDGE
        ]
        if judge_reviews:
            return sum(r.score for r in judge_reviews) / len(judge_reviews)
        if opportunity.committee_reviews:
            return sum(r.score for r in opportunity.committee_reviews) / len(
                opportunity.committee_reviews
            )
        return 0.0

    def get_opportunity(self, opportunity_id: str) -> ResearchOpportunity | None:
        return self._opportunities.get(opportunity_id)
