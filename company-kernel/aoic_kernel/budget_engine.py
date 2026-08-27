from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aoic_kernel.models import BudgetEntry
from aoic_kernel.exceptions import BudgetExceeded


class BudgetEngine:
    """Reservations, hard caps, forecasts and kill switches."""

    def __init__(self) -> None:
        self._budgets: dict[str, BudgetEntry] = {}
        self._idempotency: set[str] = set()
        self._executed: dict[str, Any] = {}

    def register(self, budget: BudgetEntry) -> None:
        self._budgets[budget.budget_id] = budget

    def reserve(self, budget_id: str, amount: float) -> BudgetEntry:
        budget = self._budgets[budget_id]
        if budget.hard_cap and budget.consumed + amount > budget.allocated:
            raise BudgetExceeded(
                f"Budget {budget_id} cap {budget.allocated} would be exceeded by {budget.consumed + amount}"
            )
        budget.consumed += amount
        return budget

    def check_action(
        self,
        budget_id: str,
        cost: float,
        action: str,
        idempotency_key: str | None = None,
    ) -> bool:
        """Return True if the action may proceed; raises BudgetExceeded if not.

        If an idempotency_key is supplied and already executed, return the
        cached outcome without re-spending budget.
        """
        if idempotency_key and idempotency_key in self._idempotency:
            return True

        budget = self._budgets[budget_id]
        if budget.hard_cap and budget.consumed + cost > budget.allocated:
            raise BudgetExceeded(
                f"Budget {budget_id} would exceed allocated {budget.allocated}"
            )

        budget.consumed += cost
        if idempotency_key:
            self._idempotency.add(idempotency_key)
            self._executed[idempotency_key] = action
        return True

    def spent(self, budget_id: str) -> float:
        return self._budgets[budget_id].consumed

    def is_duplicate(self, idempotency_key: str) -> bool:
        return idempotency_key in self._idempotency
