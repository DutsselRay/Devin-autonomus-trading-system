from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from aoic_kernel.models import CustomerSubscription, SupportTicket


class BillingSupport:
    """Shadow-mode billing and support records; no real payment processing."""

    def __init__(self) -> None:
        self._subscriptions: dict[str, CustomerSubscription] = {}
        self._tickets: dict[str, SupportTicket] = {}

    def register_subscription(
        self,
        customer_id: str,
        plan: str,
        price: float,
        currency: str = "EUR",
        billing_cycle: str = "monthly",
    ) -> CustomerSubscription:
        sub = CustomerSubscription(
            subscription_id=f"SUB-{uuid.uuid4().hex[:12]}",
            customer_id=customer_id,
            plan=plan,
            start_date=datetime.now(timezone.utc),
            price=price,
            currency=currency,
            billing_cycle=billing_cycle,
        )
        self._subscriptions[sub.subscription_id] = sub
        return sub

    def create_ticket(
        self,
        customer_id: str,
        subject: str,
        severity: str,
        evidence_links: list[str] | None = None,
    ) -> SupportTicket:
        ticket = SupportTicket(
            ticket_id=f"TKT-{uuid.uuid4().hex[:12]}",
            customer_id=customer_id,
            subject=subject,
            severity=severity,
            created_at=datetime.now(timezone.utc),
            evidence_links=evidence_links or [],
        )
        self._tickets[ticket.ticket_id] = ticket
        return ticket

    def resolve_ticket(self, ticket_id: str) -> SupportTicket:
        ticket = self._tickets.get(ticket_id)
        if ticket is None:
            raise KeyError(f"Unknown ticket {ticket_id}")
        ticket.status = "RESOLVED"
        ticket.resolved_at = datetime.now(timezone.utc)
        return ticket

    def list_open_tickets(self) -> list[SupportTicket]:
        return [t for t in self._tickets.values() if t.status in {"OPEN", "PENDING"}]

    def list_subscriptions(self) -> list[CustomerSubscription]:
        return list(self._subscriptions.values())
