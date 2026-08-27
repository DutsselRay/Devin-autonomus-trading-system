from __future__ import annotations

from datetime import datetime
from typing import Any

from aoic_kernel.models import ResearchOpportunity
from aoic_kernel.calibration import CalibrationEngine


class ResearchPublicationGate:
    """Research publication gate: probability > 0.90, calibration, sample size and committee."""

    PROBABILITY_GATE = 0.90
    MIN_SAMPLE_SIZE = 30

    def __init__(self, calibration_engine: CalibrationEngine) -> None:
        self.calibration_engine = calibration_engine

    def evaluate(
        self,
        opportunity: ResearchOpportunity,
        calibration_id: str | None = None,
    ) -> dict[str, Any]:
        """Return PASS or ABSTAIN with reasons."""
        reasons: list[str] = []

        if opportunity.probability is None or opportunity.probability <= self.PROBABILITY_GATE:
            reasons.append(
                f"probability {opportunity.probability} not above gate {self.PROBABILITY_GATE}"
            )

        if opportunity.sample_size is None or opportunity.sample_size < self.MIN_SAMPLE_SIZE:
            reasons.append(
                f"sample size {opportunity.sample_size} below minimum {self.MIN_SAMPLE_SIZE}"
            )

        if opportunity.committee_reviews:
            dissent = [r for r in opportunity.committee_reviews if r.dissent]
            risk = [r for r in opportunity.committee_reviews if r.role.value == "RISK"]
            if dissent:
                reasons.append(f"committee dissent present: {len(dissent)}")
            if risk and risk[0].score < 0:
                reasons.append("risk review negative")
        else:
            reasons.append("no committee review")

        if calibration_id:
            calibrated_prob, meta = self.calibration_engine.calibrate(
                opportunity.probability or 0.0, calibration_id
            )
            opportunity.calibration_score = meta.get("expected_calibration_error")
            if meta.get("abstain"):
                reasons.append(f"calibration abstains: {meta['reason']}")

        if reasons:
            opportunity.status = "ABSTAINED"
            return {"status": "ABSTAIN", "reasons": reasons}

        opportunity.status = "PUBLISHED"
        return {"status": "PASS", "published_probability": opportunity.probability}
