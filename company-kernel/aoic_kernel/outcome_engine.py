from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from aoic_kernel.models import DurableLearning, Outcome, Prediction, ResearchOpportunity


class OutcomeEngine:
    """Outcome attribution, hit-rate tracking and durable-learning promotion."""

    MIN_SAMPLE_SIZE = 30

    def __init__(self, min_sample_size: int = 30) -> None:
        self._outcomes: dict[str, Outcome] = {}
        self._learnings: dict[str, DurableLearning] = {}
        self.min_sample_size = min_sample_size

    def record_outcome(
        self,
        outcome_id: str,
        prediction: Prediction,
        observed_at: datetime,
        actual_return: float | None = None,
        threshold: float = 0.0,
    ) -> Outcome:
        hit = None
        if actual_return is not None:
            hit = actual_return > threshold
        outcome = Outcome(
            outcome_id=outcome_id,
            prediction_id=prediction.prediction_id,
            entity_id=prediction.entity_id,
            as_of=prediction.as_of,
            horizon=prediction.horizon,
            observed_at=observed_at,
            actual_return=actual_return,
            hit=hit,
        )
        self._outcomes[outcome_id] = outcome
        return outcome

    def outcomes_for_pattern(
        self,
        pattern_id: str,
        predictions: list[Prediction] | None = None,
    ) -> list[Outcome]:
        if predictions is None:
            return list(self._outcomes.values())
        pred_ids = {p.prediction_id for p in predictions if p.prediction_id}
        return [o for o in self._outcomes.values() if o.prediction_id in pred_ids]

    def hit_rate(
        self,
        outcomes: list[Outcome],
    ) -> float | None:
        scored = [o for o in outcomes if o.hit is not None]
        if not scored:
            return None
        return sum(1 for o in scored if o.hit) / len(scored)

    def brier_score(
        self,
        predictions: list[Prediction],
        outcomes: list[Outcome],
    ) -> float | None:
        pairs = self._match(predictions, outcomes)
        if not pairs:
            return None
        return sum((p.probability - (1 if o.hit else 0)) ** 2 for p, o in pairs) / len(pairs)

    def propose_learning(
        self,
        learning_id: str,
        pattern_id: str,
        experiment_id: str,
        hypothesis: str,
        evidence: list[str],
        replicators: list[str],
    ) -> DurableLearning | None:
        """Promote a proposed learning only after independent replication and sample size."""
        if len(replicators) < 1:
            return None
        if len(evidence) < self.min_sample_size:
            return None
        learning = DurableLearning(
            learning_id=learning_id,
            pattern_id=pattern_id,
            experiment_id=experiment_id,
            hypothesis=hypothesis,
            evidence=evidence,
            effective_sample_size=len(evidence),
            validated_by=replicators,
            status="REPLICATED",
        )
        self._learnings[learning_id] = learning
        return learning

    def approve_learning(self, learning_id: str, approver: str) -> DurableLearning:
        learning = self._learnings[learning_id]
        if learning.status != "REPLICATED":
            raise ValueError("Learning must be replicated before approval")
        learning.status = "APPROVED"
        learning.validated_by.append(approver)
        return learning

    def snapshot(self) -> dict[str, Any]:
        return {
            "outcomes": [o.model_dump() for o in self._outcomes.values()],
            "learnings": [l.model_dump() for l in self._learnings.values()],
        }

    @staticmethod
    def _match(
        predictions: list[Prediction], outcomes: list[Outcome]
    ) -> list[tuple[Prediction, Outcome]]:
        pred_by_id = {p.prediction_id: p for p in predictions if p.prediction_id}
        pairs: list[tuple[Prediction, Outcome]] = []
        for o in outcomes:
            p = pred_by_id.get(o.prediction_id)
            if p is not None and o.hit is not None:
                pairs.append((p, o))
        return pairs
