from __future__ import annotations

from typing import Any

from aoic_kernel.models import AgentCharter, Authority, DecisionProposal, PolicyRule, RiskLevel
from aoic_kernel.exceptions import PolicyViolation


class PolicyEngine:
    """Versioned policy-as-code and pre-action enforcement."""

    def __init__(self) -> None:
        self._rules: list[PolicyRule] = []

    def register(self, rule: PolicyRule) -> None:
        self._rules.append(rule)

    def evaluate(self, proposal: DecisionProposal, context: dict[str, Any] | None = None) -> None:
        ctx = context or {}
        for rule in self._rules:
            if not self._applies(rule, proposal, ctx):
                continue
            if rule.effect == "DENY":
                raise PolicyViolation(f"Policy {rule.policy_id} denies this action")
            if rule.effect == "ESCALATE":
                # Escalation means required authority must be at least rule.authority_min
                if _authority_lt(proposal.required_authority, rule.authority_min):
                    raise PolicyViolation(
                        f"Policy {rule.policy_id} requires authority {rule.authority_min}"
                    )

    def _applies(self, rule: PolicyRule, proposal: DecisionProposal, context: dict[str, Any]) -> bool:
        return True  # Simplified: in production use policy condition DSL


def _authority_lt(a: Authority, b: Authority) -> bool:
    order = ["A0", "A1", "A2", "A3", "A4", "A5"]
    return order.index(a.value) < order.index(b.value)
