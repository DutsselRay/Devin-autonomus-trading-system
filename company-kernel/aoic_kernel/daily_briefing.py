from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from aoic_kernel.models import DecisionProposal, RiskLevel, Reversibility


class HumanAttentionScore:
    """Rank proposals by materiality, irreversibility, legal exposure, capital at risk,
    strategic impact, uncertainty and urgency.
    """

    _REVERSIBILITY = {"HIGH": 1, "MEDIUM": 2, "LOW": 3, "NONE": 4}
    _RISK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "UNKNOWN": 3}

    def score(self, proposal: DecisionProposal) -> float:
        rev = self._REVERSIBILITY.get(proposal.reversibility.value, 1)
        risk = self._RISK.get(proposal.regulatory_risk.value, 1)
        capital = self._capital_at_risk(proposal)
        materiality = min(capital / 1000.0, 10.0) if capital else 0
        confidence_penalty = (1 - (proposal.confidence or 0)) * 5
        strategic = 1 if proposal.strategic_impact else 0
        urgency = 2 if proposal.urgency == "high" else 1 if proposal.urgency == "medium" else 0
        return rev + risk + materiality + confidence_penalty + strategic + urgency

    def _capital_at_risk(self, proposal: DecisionProposal) -> float:
        ev = proposal.expected_value
        if ev.base is not None and ev.low is not None and ev.low < 0:
            return abs(ev.low)
        return proposal.cost.one_off or 0


class DailyBriefing:
    """Produces a human-principal daily briefing with ranked proposals, incidents and
    a no-decision section."""

    def __init__(self, attention: HumanAttentionScore | None = None) -> None:
        self.attention = attention or HumanAttentionScore()
        self._proposals: list[DecisionProposal] = []
        self._incidents: list[dict[str, Any]] = []
        self.no_decision: list[dict[str, Any]] = []
        self.max_proposals = 10

    def add_proposal(self, proposal: DecisionProposal) -> None:
        self._proposals.append(proposal)

    def add_incident(self, incident: dict[str, Any]) -> None:
        self._incidents.append(incident)

    def generate(
        self,
        proposals: list[DecisionProposal] | None = None,
        incidents: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        candidates = proposals or self._proposals
        incidents = incidents or self._incidents
        ranked = sorted(candidates, key=self.attention.score, reverse=True)
        top = ranked[: self.max_proposals]
        overflow = ranked[self.max_proposals :]
        return {
            "date": datetime.now(timezone.utc).isoformat(),
            "ranked_proposals": [p.model_dump() for p in top],
            "overflow": [p.decision_id for p in overflow],
            "incidents": incidents,
            "no_decision_required": self.no_decision,
            "attention_load": {
                "total": len(candidates),
                "presented": len(top),
                "target": 3,
                "cap": self.max_proposals,
            },
        }

    def is_within_target(self) -> bool:
        return len(self._proposals) <= 3
