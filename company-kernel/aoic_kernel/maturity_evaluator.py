from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from aoic_kernel.models import MaturityCriterion, MaturityLevel, MaturityScore


REQUIRED_MATURITY_CRITERIA = [
    ("C1", "Constitutional constraints are technically enforced and adversarially tested."),
    ("C2", "Every material decision is reproducible from PIT evidence and versioned code."),
    ("C3", "The Opportunity Engine beats approved simple baselines across sealed OOS, regimes and shadow-live operation after realistic costs."),
    ("C4", "Probabilities are calibrated; abstention works; the publication gate cannot be bypassed."),
    ("C5", "Compliance, data rights, PSP acceptance, claims and jurisdiction scope are approved before monetization."),
    ("C6", "Agent evolution uses fixed evals, shadow/canary deployment and reliable rollback without self-granted authority."),
    ("C7", "Critical incidents are zero or contained and learned from within defined SLOs."),
    ("C8", "Human attention remains ≤10 material decisions/day with no hidden escalation debt."),
    ("C9", "Memory is compact yet sufficient for reconstruction, audit and cumulative learning."),
    ("C10", "Unit economics survive downside assumptions including licensing, CAC, legal and operational costs."),
    ("C11", "Customers receive clear, useful, non-manipulative research and visible corrections."),
    ("C12", "The organization can replace a model, vendor or agent without losing its institutional knowledge."),
]


class MaturityEvaluator:
    """Section 40 10/10 maturity scorecard."""

    def __init__(self) -> None:
        self._criteria: dict[str, MaturityCriterion] = {
            criterion_id: MaturityCriterion(
                criterion_id=criterion_id,
                name=criterion_id,
                description=description,
            )
            for criterion_id, description in REQUIRED_MATURITY_CRITERIA
        }

    def list_criteria(self) -> list[MaturityCriterion]:
        return list(self._criteria.values())

    def get(self, criterion_id: str) -> MaturityCriterion:
        if criterion_id not in self._criteria:
            raise KeyError(criterion_id)
        return self._criteria[criterion_id]

    def submit_evidence(
        self,
        criterion_id: str,
        level: MaturityLevel,
        evidence: list[str],
    ) -> MaturityCriterion:
        if criterion_id not in self._criteria:
            raise KeyError(criterion_id)
        if not evidence:
            raise ValueError("maturity evidence is required")
        criterion = self._criteria[criterion_id]
        criterion.level = level
        criterion.evidence.extend(evidence)
        criterion.updated_at = datetime.now(timezone.utc)
        self._criteria[criterion_id] = criterion
        return criterion

    def evaluate(self) -> MaturityScore:
        criteria = list(self._criteria.values())
        values = {MaturityLevel.FAIL: 0.0, MaturityLevel.PARTIAL: 0.5, MaturityLevel.PASS: 1.0}
        average = sum(values[c.level] for c in criteria) / len(criteria)
        overall = all(c.level == MaturityLevel.PASS for c in criteria)
        return MaturityScore(
            scorecard_id=f"SC-{uuid4().hex[:8].upper()}",
            evaluated_at=datetime.now(timezone.utc),
            criteria=criteria,
            overall_10_of_10=overall,
            average=average if not overall else 1.0,
        )
