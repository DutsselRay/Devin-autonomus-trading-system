from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from aoic_kernel.commercial_readiness import CommercialReadiness
from aoic_kernel.models import LaunchDecision


class A5Launch:
    """Human A5 launch decision gate. No agent may approve a commercial launch."""

    def __init__(self, commercial_readiness: CommercialReadiness) -> None:
        self.readiness = commercial_readiness
        self._decisions: dict[str, LaunchDecision] = {}

    def request_launch(self, rationale: str = "") -> LaunchDecision:
        decision = LaunchDecision(
            decision_id=f"A5L-{uuid.uuid4().hex[:12]}",
            status="PENDING",
            gates=list(self.readiness.required_gates),
            rationale=rationale,
        )
        self._decisions[decision.decision_id] = decision
        return decision

    def approve(self, decision_id: str, human_principal: str) -> LaunchDecision:
        if not self.readiness.is_ready():
            raise ValueError("commercial readiness gates are not all passed")
        decision = self._decisions.get(decision_id)
        if decision is None:
            raise KeyError(f"Unknown launch decision {decision_id}")
        decision.status = "APPROVED"
        decision.approved_by = human_principal
        decision.approved_at = datetime.now(timezone.utc)
        return decision

    def deny(self, decision_id: str, human_principal: str, rationale: str = "") -> LaunchDecision:
        decision = self._decisions.get(decision_id)
        if decision is None:
            raise KeyError(f"Unknown launch decision {decision_id}")
        decision.status = "DENIED"
        decision.approved_by = human_principal
        decision.approved_at = datetime.now(timezone.utc)
        decision.rationale = rationale
        return decision

    def get(self, decision_id: str) -> LaunchDecision | None:
        return self._decisions.get(decision_id)


class CustomerWeb:
    """Static, evidence-linked customer-facing page generator (shadow mode)."""

    def __init__(self, public_track_record: Any | None = None) -> None:
        self.public_track_record = public_track_record
        self._pages: dict[str, dict[str, Any]] = {}

    def publish_page(
        self,
        page_id: str,
        title: str,
        content: str,
        evidence_links: list[str],
    ) -> dict[str, Any]:
        if not evidence_links:
            raise ValueError("customer-facing page must include evidence links")
        page = {
            "page_id": page_id,
            "title": title,
            "content": content,
            "evidence_links": evidence_links,
            "published_at": datetime.now(timezone.utc),
        }
        self._pages[page_id] = page
        return page

    def get_page(self, page_id: str) -> dict[str, Any] | None:
        return self._pages.get(page_id)

    def list_pages(self) -> list[dict[str, Any]]:
        return list(self._pages.values())
